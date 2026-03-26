from django.contrib import admin
from .models import Category, Ticket, TicketComment, TicketHistory


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'priority_weight', 'is_critical', 'created_at']
    list_filter = ['is_critical', 'created_at']
    search_fields = ['name', 'description']


class TicketCommentInline(admin.TabularInline):
    model = TicketComment
    extra = 1


class TicketHistoryInline(admin.TabularInline):
    model = TicketHistory
    extra = 0
    readonly_fields = ['user', 'action', 'old_value', 'new_value', 'created_at']


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'status', 'priority_score', 'created_by', 'created_at']
    list_filter = ['status', 'category', 'created_at', 'neighborhood']
    search_fields = ['title', 'description', 'address', 'created_by__username']
    readonly_fields = ['priority_score', 'created_at']
    inlines = [TicketCommentInline, TicketHistoryInline]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('title', 'description', 'category')
        }),
        ('Localização', {
            'fields': ('address', 'neighborhood', 'latitude', 'longitude')
        }),
        ('Mídia', {
            'fields': ('photo',)
        }),
        ('Métricas', {
            'fields': ('affected_people_estimate', 'priority_score')
        }),
        ('Status e Análise', {
            'fields': ('status', 'analyst', 'rejection_reason')
        }),
        ('Datas', {
            'fields': ('created_at', 'analyzed_at', 'started_at', 'completed_at')
        }),
    )


@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['comment', 'ticket__title', 'user__username']


@admin.register(TicketHistory)
class TicketHistoryAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'user', 'action', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['ticket__title', 'user__username']