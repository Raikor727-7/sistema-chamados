from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    path('', views.ticket_list, name='ticket_list'),
    path('criar/', views.ticket_create, name='ticket_create'),
    path('<int:pk>/', views.ticket_detail, name='ticket_detail'),
    path('<int:pk>/gerenciar/', views.ticket_manage, name='ticket_manage'),
    path('dashboard/', views.ticket_dashboard, name='dashboard'),
]