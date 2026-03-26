from django import forms
from .models import Ticket, TicketComment, Category


class TicketForm(forms.ModelForm):
    """Formulário para criação de tickets"""
    
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'category', 'address', 'neighborhood', 
                  'latitude', 'longitude', 'photo', 'affected_people_estimate']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Poste queimado na Rua das Flores'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descreva detalhadamente o problema...'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Rua, número, complemento...'
            }),
            'neighborhood': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Centro, Jardim América...'
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': 'any',
                'placeholder': 'Latitude (opcional)'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': 'any',
                'placeholder': 'Longitude (opcional)'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'affected_people_estimate': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'value': 1
            }),
        }
    
    def __init__(self, *args, **kwargs):
        # Remove 'user' do kwargs se existir
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Se o usuário estiver autenticado, podemos pré-preencher alguns campos
        if user and user.address:
            self.fields['address'].initial = user.address
        if user and user.neighborhood:
            self.fields['neighborhood'].initial = user.neighborhood


class TicketCommentForm(forms.ModelForm):
    """Formulário para comentários nos tickets"""
    
    class Meta:
        model = TicketComment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Adicione um comentário sobre este chamado...'
            })
        }
        labels = {
            'comment': 'Seu comentário'
        }


class TicketAnalystForm(forms.ModelForm):
    """Formulário para analistas gerenciarem tickets"""
    
    class Meta:
        model = Ticket
        fields = ['status', 'analyst', 'rejection_reason']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'analyst': forms.Select(attrs={'class': 'form-select'}),
            'rejection_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rejection_reason'].required = False
        # Limitar analistas apenas aos que são do tipo analyst, manager ou admin
        from accounts.models import User
        self.fields['analyst'].queryset = User.objects.filter(
            user_type__in=['analyst', 'manager', 'admin']
        )


class TicketManagerForm(forms.ModelForm):
    """Formulário para gestores (pode editar quase tudo, exceto score)"""
    
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'category', 'address', 'neighborhood', 
                  'status', 'analyst', 'rejection_reason', 'affected_people_estimate']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'neighborhood': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'analyst': forms.Select(attrs={'class': 'form-select'}),
            'rejection_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'affected_people_estimate': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rejection_reason'].required = False
        # Limitar analistas apenas aos que são do tipo analyst, manager ou admin
        from accounts.models import User
        self.fields['analyst'].queryset = User.objects.filter(
            user_type__in=['analyst', 'manager', 'admin']
        )