from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Modelo de usuário estendido"""
    USER_TYPE_CHOICES = (
        ('citizen', 'Cidadão'),
        ('analyst', 'Analista de Ouvidoria'),
        ('manager', 'Gestor'),
        ('admin', 'Administrador'),
    )
    
    user_type = models.CharField(
        _('Tipo de usuário'),
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='citizen'
    )
    phone = models.CharField(_('Telefone'), max_length=20, blank=True)
    cpf = models.CharField(_('CPF'), max_length=14, unique=True, blank=True, null=True)
    address = models.TextField(_('Endereço'), blank=True)
    neighborhood = models.CharField(_('Bairro'), max_length=100, blank=True)
    department = models.CharField(_('Departamento'), max_length=100, blank=True, help_text='Ex: Ouvidoria, Infraestrutura, etc')
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)
    
    class Meta:
        verbose_name = _('Usuário')
        verbose_name_plural = _('Usuários')
    
    def __str__(self):
        return self.get_full_name() or self.username
    
    def is_citizen(self):
        return self.user_type == 'citizen'
    
    def is_analyst(self):
        return self.user_type in ['analyst', 'manager', 'admin']
    
    def is_manager(self):
        return self.user_type in ['manager', 'admin']
    
    def is_admin(self):
        return self.user_type == 'admin' or self.is_superuser
    
    def can_manage_tickets(self):
        """Verifica se pode gerenciar tickets (analisar, aprovar, etc)"""
        return self.user_type in ['analyst', 'manager', 'admin']
    
    def can_manage_users(self):
        """Verifica se pode gerenciar usuários"""
        return self.user_type in ['manager', 'admin']