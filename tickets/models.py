from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import math
from django.db.models.signals import post_save
from django.dispatch import receiver


class Category(models.Model):
    """Categorias de chamados com pesos para prioridade"""
    name = models.CharField('Nome', max_length=100)
    description = models.TextField('Descrição', blank=True)
    priority_weight = models.FloatField('Peso na prioridade', default=1.0, help_text='Peso para cálculo do score (0-10)')
    is_critical = models.BooleanField('É crítica?', default=False, help_text='Infraestrutura crítica')
    icon = models.CharField('Ícone', max_length=50, blank=True, help_text='Classe do ícone (FontAwesome)')
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['-is_critical', 'name']
    
    def __str__(self):
        return self.name


class Ticket(models.Model):
    """Modelo principal de chamado"""
    STATUS_CHOICES = (
        ('pending', 'Aguardando Análise'),
        ('approved', 'Aprovado'),
        ('rejected', 'Rejeitado'),
        ('in_progress', 'Em Andamento'),
        ('completed', 'Concluído'),
        ('cancelled', 'Cancelado'),
    )
    
    # Informações básicas
    title = models.CharField('Título', max_length=200)
    description = models.TextField('Descrição')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, verbose_name='Categoria')
    
    # Localização
    address = models.CharField('Endereço', max_length=255)
    neighborhood = models.CharField('Bairro', max_length=100)
    latitude = models.DecimalField('Latitude', max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField('Longitude', max_digits=10, decimal_places=7, null=True, blank=True)
    
    # Fotos
    photo = models.ImageField('Foto', upload_to='tickets/%Y/%m/', blank=True, null=True)
    
    # Usuários envolvidos
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tickets_created', verbose_name='Criado por')
    analyst = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_analyzed', verbose_name='Analista')
    
    # Datas
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    analyzed_at = models.DateTimeField('Analisado em', null=True, blank=True)
    started_at = models.DateTimeField('Iniciado em', null=True, blank=True)
    completed_at = models.DateTimeField('Concluído em', null=True, blank=True)
    
    # Status
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField('Motivo da rejeição', blank=True)
    
    # Métricas para prioridade
    affected_people_estimate = models.IntegerField('Estimativa de pessoas afetadas', default=1, help_text='Quantas pessoas são afetadas?')
    
    # Prioridade
    priority_score = models.FloatField('Score de prioridade', default=0.0, editable=False)
    
    class Meta:
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        ordering = ['-priority_score', '-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"
    
    def calculate_priority_score(self):
        """
        Calcula o score de prioridade (0-100) baseado em:
        - Risco à segurança (peso da categoria)
        - Pessoas afetadas
        - Tempo sem resolução
        - Se é crítica
        """
        # Se o ticket já foi concluído ou cancelado, prioridade é 0
        if self.status in ['completed', 'cancelled']:
            return 0.0
        
        # Fator 1: Categoria e criticidade (0-40 pontos)
        category_score = 20  # valor padrão
        if self.category:
            category_score = min(self.category.priority_weight * 4, 40)
        
        # Fator 2: Pessoas afetadas (0-30 pontos)
        people_score = min(math.log(self.affected_people_estimate + 1) * 5, 30)
        
        # Fator 3: Tempo de espera (0-30 pontos)
        # Se ainda não tem created_at (objeto novo), considera 0 dias
        time_score = 0
        if self.created_at:
            days_waiting = (timezone.now() - self.created_at).days
            time_score = min(days_waiting * 2, 30)
        
        # Total
        total_score = category_score + people_score + time_score
        
        # Bônus se for crítica
        if self.category and self.category.is_critical:
            total_score = min(total_score + 10, 100)
        
        return round(total_score, 2)
    
    def save(self, *args, **kwargs):
        # Para objetos novos, primeiro salva para ter created_at
        is_new = self.pk is None
        
        if is_new:
            # Salva sem o score primeiro
            super().save(*args, **kwargs)
            # Agora que tem created_at, calcula e atualiza o score
            self.priority_score = self.calculate_priority_score()
            # Salva novamente apenas com o score atualizado
            super().save(update_fields=['priority_score'])
        else:
            # Para objetos existentes, calcula e salva normalmente
            self.priority_score = self.calculate_priority_score()
            super().save(*args, **kwargs)
    
    def approve(self, analyst):
        """Aprova o ticket"""
        self.status = 'approved'
        self.analyst = analyst
        self.analyzed_at = timezone.now()
        self.save()
    
    def reject(self, analyst, reason):
        """Rejeita o ticket"""
        self.status = 'rejected'
        self.analyst = analyst
        self.analyzed_at = timezone.now()
        self.rejection_reason = reason
        self.save()
    
    def start_work(self):
        """Inicia o trabalho no ticket"""
        self.status = 'in_progress'
        self.started_at = timezone.now()
        self.save()
    
    def complete(self):
        """Completa o ticket"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()


class TicketComment(models.Model):
    """Comentários nos tickets"""
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments', verbose_name='Ticket')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Usuário')
    comment = models.TextField('Comentário')
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Comentário'
        verbose_name_plural = 'Comentários'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comentário de {self.user.get_full_name()} em {self.ticket}"


class TicketHistory(models.Model):
    """Histórico de alterações dos tickets"""
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='history', verbose_name='Ticket')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Usuário')
    action = models.CharField('Ação', max_length=100)
    old_value = models.TextField('Valor antigo', blank=True)
    new_value = models.TextField('Valor novo', blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Histórico'
        verbose_name_plural = 'Históricos'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.action} - {self.ticket}"