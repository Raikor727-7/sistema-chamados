from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from tickets import views

urlpatterns = [
    path('admin/', admin.site.urls), # painel admin do django
    path('', views.home, name='home'), # pagina inicial
    path('tickets/', include('tickets.urls')), # urls do tickets
    path('accounts/', include('accounts.urls')), # urls da account
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)