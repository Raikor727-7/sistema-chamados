from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'user_type', 'department', 'is_active', 'status_badges']
    list_filter = ['user_type', 'is_active', 'is_staff', 'department']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'cpf']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Pessoais', {
            'fields': ('phone', 'cpf', 'address', 'neighborhood')
        }),
        ('Informações Profissionais', {
            'fields': ('user_type', 'department'),
            'classes': ('wide',)
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informações Pessoais', {
            'fields': ('phone', 'cpf', 'address', 'neighborhood', 'user_type', 'department')
        }),
    )
    
    def status_badges(self, obj):
        """Mostra badges de status para o usuário"""
        badges = []
        
        # Badge de tipo de usuário
        if obj.user_type == 'analyst':
            badges.append('<span class="badge bg-info" style="margin-right: 5px;">Analista</span>')
        elif obj.user_type == 'manager':
            badges.append('<span class="badge bg-warning" style="margin-right: 5px;">Gestor</span>')
        elif obj.user_type == 'admin':
            badges.append('<span class="badge bg-danger" style="margin-right: 5px;">Admin</span>')
        else:
            badges.append('<span class="badge bg-secondary" style="margin-right: 5px;">Cidadão</span>')
        
        # Badge de status ativo/inativo
        if obj.is_active:
            badges.append('<span class="badge bg-success">Ativo</span>')
        else:
            badges.append('<span class="badge bg-danger">Inativo</span>')
        
        # Usar mark_safe para renderizar HTML
        return mark_safe(' '.join(badges))
    
    status_badges.short_description = 'Status'
    status_badges.admin_order_field = 'user_type'
    
    actions = ['make_analyst', 'make_manager']
    
    def make_analyst(self, request, queryset):
        """Ação para promover usuários a analista"""
        updated = queryset.update(user_type='analyst')
        self.message_user(request, f'{updated} usuário(s) promovido(s) a Analista.')
    make_analyst.short_description = 'Promover para Analista'
    
    def make_manager(self, request, queryset):
        """Ação para promover usuários a gestor"""
        updated = queryset.update(user_type='manager')
        self.message_user(request, f'{updated} usuário(s) promovido(s) a Gestor.')
    make_manager.short_description = 'Promover para Gestor'