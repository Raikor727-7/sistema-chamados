from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('cadastrar/', views.register, name='register'),
    path('entrar/', views.login_view, name='login'),
    path('sair/', views.logout_view, name='logout'),
    path('perfil/', views.profile, name='profile'),
    path('meus-chamados/', views.my_tickets, name='my_tickets'),
    path('editar-perfil/', views.edit_profile, name='edit_profile'),
    # Novas rotas para gestão
    path('usuarios/', views.user_list, name='user_list'),
    path('usuarios/criar/', views.user_create_analyst, name='user_create_analyst'),
    path('usuarios/<int:pk>/editar/', views.user_edit, name='user_edit'),
    path('usuarios/<int:pk>/deletar/', views.user_delete, name='user_delete'),
]