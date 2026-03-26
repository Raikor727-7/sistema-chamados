from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Ticket, Category, TicketHistory
from .forms import TicketForm, TicketCommentForm, TicketAnalystForm, TicketManagerForm
from accounts.models import User

from tickets import models

def home(request):
    """Página inicial"""
    from django.db.models import Count
    
    total_tickets = Ticket.objects.count()
    pending_tickets = Ticket.objects.filter(status='pending').count()
    in_progress_tickets = Ticket.objects.filter(status='in_progress').count()
    completed_tickets = Ticket.objects.filter(status='completed').count()
    
    context = {
        'total_tickets': total_tickets,
        'pending_tickets': pending_tickets,
        'in_progress_tickets': in_progress_tickets,
        'completed_tickets': completed_tickets,
    }
    return render(request, 'home.html', context)


@login_required
def ticket_list(request):
    """Lista de tickets"""
    tickets = Ticket.objects.all()
    
    # Filtros
    status_filter = request.GET.get('status')
    category_filter = request.GET.get('category')
    search_query = request.GET.get('search')
    
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    if category_filter:
        tickets = tickets.filter(category_id=category_filter)
    if search_query:
        tickets = tickets.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(address__icontains=search_query)
        )
    
    # Paginação
    paginator = Paginator(tickets, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.all()
    
    context = {
        'tickets': page_obj,
        'categories': categories,
        'status_choices': Ticket.STATUS_CHOICES,
    }
    return render(request, 'tickets/list.html', context)


@login_required
def ticket_create(request):
    """Criação de novo ticket"""
    if request.method == 'POST':
        form = TicketForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user
            ticket.save()
            messages.success(request, '✅ Chamado criado com sucesso! Você receberá atualizações por e-mail.')
            return redirect('tickets:ticket_detail', pk=ticket.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'❌ Erro no campo {field}: {error}')
    else:
        # Pré-preenche com dados do usuário se disponíveis
        initial_data = {}
        if request.user.address:
            initial_data['address'] = request.user.address
        if request.user.neighborhood:
            initial_data['neighborhood'] = request.user.neighborhood
        
        form = TicketForm(initial=initial_data, user=request.user)
    
    return render(request, 'tickets/create.html', {'form': form})


@login_required
def ticket_detail(request, pk):
    """Detalhes do ticket"""
    ticket = get_object_or_404(Ticket, pk=pk)
    
    if request.method == 'POST':
        form = TicketCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.ticket = ticket
            comment.user = request.user
            comment.save()
            messages.success(request, '💬 Comentário adicionado com sucesso!')
            return redirect('tickets:ticket_detail', pk=ticket.pk)
        else:
            messages.error(request, '❌ Erro ao adicionar comentário.')
    else:
        form = TicketCommentForm()
    
    context = {
        'ticket': ticket,
        'form': form,
    }
    return render(request, 'tickets/detail.html', context)

# Decoradores personalizados
def analyst_required(view_func):
    """Decorador para verificar se o usuário é analista ou superior"""
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.can_manage_tickets():
            return view_func(request, *args, **kwargs)
        messages.error(request, 'Você não tem permissão para acessar esta área.')
        return redirect('home')
    return wrapper


def manager_required(view_func):
    """Decorador para verificar se o usuário é gestor ou superior"""
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_manager():
            return view_func(request, *args, **kwargs)
        messages.error(request, 'Acesso restrito a gestores.')
        return redirect('home')
    return wrapper


@login_required
@analyst_required
def ticket_manage(request, pk):
    """Página de gestão de ticket (analistas)"""
    ticket = get_object_or_404(Ticket, pk=pk)
    
    if request.method == 'POST':
        if request.user.is_manager():
            form = TicketManagerForm(request.POST, instance=ticket)
        else:
            form = TicketAnalystForm(request.POST, instance=ticket)
        
        if form.is_valid():
            old_status = ticket.status
            ticket = form.save(commit=False)
            
            # Se o status mudou, registra no histórico
            if old_status != ticket.status:
                # Registrar a mudança de status
                TicketHistory.objects.create(
                    ticket=ticket,
                    user=request.user,
                    action=f'Mudança de status: {old_status} -> {ticket.status}',
                    old_value=old_status,
                    new_value=ticket.status
                )
                
                # Atualizar datas conforme status
                if ticket.status == 'approved':
                    ticket.analyzed_at = timezone.now()
                elif ticket.status == 'in_progress':
                    ticket.started_at = timezone.now()
                elif ticket.status == 'completed':
                    ticket.completed_at = timezone.now()
            
            ticket.save()
            messages.success(request, 'Ticket atualizado com sucesso!')
            return redirect('tickets:ticket_detail', pk=ticket.pk)
    else:
        if request.user.is_manager():
            form = TicketManagerForm(instance=ticket)
        else:
            form = TicketAnalystForm(instance=ticket)
    
    context = {
        'ticket': ticket,
        'form': form,
        'is_manager': request.user.is_manager(),
    }
    return render(request, 'tickets/manage.html', context)


@login_required
@manager_required
def user_list(request):
    """Lista de usuários para gestão"""
    users = User.objects.all().order_by('-date_joined')
    
    # Filtros
    user_type = request.GET.get('user_type')
    if user_type:
        users = users.filter(user_type=user_type)
    
    search = request.GET.get('search')
    if search:
        users = users.filter(
            models.Q(username__icontains=search) |
            models.Q(first_name__icontains=search) |
            models.Q(email__icontains=search)
        )
    
    context = {
        'users': users,
        'total_users': users.count(),
        'citizens': users.filter(user_type='citizen').count(),
        'analysts': users.filter(user_type='analyst').count(),
        'managers': users.filter(user_type='manager').count(),
    }
    return render(request, 'accounts/user_list.html', context)


@login_required
@manager_required
def user_create_analyst(request):
    """Criar novo analista ou gestor"""
    if request.method == 'POST':
        from accounts.forms import CitizenRegistrationForm
        
        form = CitizenRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.user_type = request.POST.get('user_type', 'analyst')
            user.department = request.POST.get('department', 'Ouvidoria')
            user.is_staff = True  # Analistas têm acesso ao admin
            user.save()
            messages.success(request, f'Usuário {user.get_full_name()} criado com sucesso!')
            return redirect('accounts:user_list')
    else:
        from accounts.forms import CitizenRegistrationForm
        form = CitizenRegistrationForm()
    
    return render(request, 'accounts/create_user.html', {'form': form})


@login_required
@manager_required
def user_edit(request, pk):
    """Editar usuário"""
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.phone = request.POST.get('phone')
        user.user_type = request.POST.get('user_type')
        user.department = request.POST.get('department')
        user.is_active = request.POST.get('is_active') == 'on'
        
        if request.user.is_superuser:
            user.is_staff = request.POST.get('is_staff') == 'on'
        
        user.save()
        messages.success(request, 'Usuário atualizado com sucesso!')
        return redirect('accounts:user_list')
    
    context = {'edit_user': user}
    return render(request, 'accounts/edit_user.html', context)


@login_required
@manager_required
def user_delete(request, pk):
    """Desativar/ativar usuário"""
    user = get_object_or_404(User, pk=pk)
    
    if user == request.user:
        messages.error(request, 'Você não pode desativar seu próprio usuário.')
    else:
        user.is_active = not user.is_active
        user.save()
        status = 'ativado' if user.is_active else 'desativado'
        messages.success(request, f'Usuário {user.get_full_name()} {status} com sucesso!')
    
    return redirect('accounts:user_list')


@login_required
@analyst_required
def ticket_dashboard(request):
    """Dashboard para analistas e gestores"""
    from django.db.models import Count, Q
    
    # Estatísticas gerais
    total_tickets = Ticket.objects.count()
    pending_tickets = Ticket.objects.filter(status='pending').count()
    in_progress_tickets = Ticket.objects.filter(status='in_progress').count()
    completed_tickets = Ticket.objects.filter(status='completed').count()
    
    # Tickets por categoria
    tickets_by_category = Category.objects.annotate(
        total=Count('ticket')
    ).filter(total__gt=0)
    
    # Tickets por bairro (top 5)
    tickets_by_neighborhood = Ticket.objects.values('neighborhood').annotate(
        total=Count('id')
    ).order_by('-total')[:5]
    
    # Tickets com maior prioridade
    high_priority_tickets = Ticket.objects.filter(
        status__in=['pending', 'approved', 'in_progress']
    ).order_by('-priority_score')[:10]
    
    context = {
        'total_tickets': total_tickets,
        'pending_tickets': pending_tickets,
        'in_progress_tickets': in_progress_tickets,
        'completed_tickets': completed_tickets,
        'tickets_by_category': tickets_by_category,
        'tickets_by_neighborhood': tickets_by_neighborhood,
        'high_priority_tickets': high_priority_tickets,
    }
    return render(request, 'tickets/dashboard.html', context)