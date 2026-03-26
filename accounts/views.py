from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from .forms import CitizenRegistrationForm, CustomAuthenticationForm
from .models import User


def register(request):
    """Cadastro de novos cidadãos"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = CitizenRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Faz login automático após cadastro
            login(request, user)
            messages.success(request, f'Bem-vindo(a) {user.get_full_name()}! Seu cadastro foi realizado com sucesso.')
            return redirect('home')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CitizenRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """Login de usuários"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Bem-vindo(a) de volta, {user.get_full_name() or user.username}!')
            
            # Redireciona para página anterior se existir
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('home')
        else:
            messages.error(request, 'Usuário ou senha inválidos.')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """Logout de usuários"""
    logout(request)
    messages.info(request, 'Você saiu do sistema com sucesso.')
    return redirect('home')


@login_required
def profile(request):
    """Perfil do usuário"""
    return render(request, 'accounts/profile.html')


@login_required
def my_tickets(request):
    """Meus chamados"""
    from tickets.models import Ticket
    tickets = Ticket.objects.filter(created_by=request.user).order_by('-created_at')
    
    context = {
        'tickets': tickets,
        'total': tickets.count(),
        'pending': tickets.filter(status='pending').count(),
        'in_progress': tickets.filter(status='in_progress').count(),
        'completed': tickets.filter(status='completed').count(),
    }
    return render(request, 'accounts/my_tickets.html', context)


@login_required
def edit_profile(request):
    """Editar perfil do usuário"""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.phone = request.POST.get('phone')
        user.address = request.POST.get('address')
        user.neighborhood = request.POST.get('neighborhood')
        user.save()
        messages.success(request, 'Perfil atualizado com sucesso!')
        return redirect('profile')
    
    return render(request, 'accounts/edit_profile.html')


# ============== NOVAS VIEWS PARA GESTÃO ==============

def manager_required(view_func):
    """Decorador para verificar se o usuário é gestor ou superior"""
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_manager() or request.user.is_superuser):
            return view_func(request, *args, **kwargs)
        messages.error(request, 'Acesso restrito a gestores.')
        return redirect('home')
    return wrapper


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
        'citizens': User.objects.filter(user_type='citizen').count(),
        'analysts': User.objects.filter(user_type='analyst').count(),
        'managers': User.objects.filter(user_type='manager').count(),
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
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
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