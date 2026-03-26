from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from .models import User


class CitizenRegistrationForm(UserCreationForm):
    """Formulário de cadastro para cidadãos"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'seu@email.com'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Seu nome'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Seu sobrenome'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '(00) 00000-0000'
        })
    )
    cpf = forms.CharField(
        max_length=14,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '000.000.000-00'
        })
    )
    address = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Rua, número, complemento...'
        })
    )
    neighborhood = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Seu bairro'
        })
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 
                  'cpf', 'address', 'neighborhood', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adicionar classes CSS aos campos
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nome de usuário'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Senha'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmar senha'
        })
    
    def clean_cpf(self):
        """Valida CPF"""
        cpf = self.cleaned_data.get('cpf')
        # Remove caracteres não numéricos
        cpf = ''.join(filter(str.isdigit, cpf))
        
        if len(cpf) != 11:
            raise forms.ValidationError('CPF inválido. Deve conter 11 dígitos.')
        
        # Verifica se CPF já existe
        if User.objects.filter(cpf=cpf).exists():
            raise forms.ValidationError('Este CPF já está cadastrado.')
        
        return cpf
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'citizen'  # Define como cidadão
        user.email = self.cleaned_data['email']
        user.cpf = self.cleaned_data['cpf']
        user.phone = self.cleaned_data['phone']
        user.address = self.cleaned_data['address']
        user.neighborhood = self.cleaned_data['neighborhood']
        
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    """Formulário de login personalizado"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Usuário ou email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Senha'
        })
    )
    
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if username and password:
            # Permite login com email ou username
            user = authenticate(username=username, password=password)
            if user is None:
                # Tenta autenticar com email
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass
            
            if user is None:
                raise forms.ValidationError('Usuário ou senha inválidos.')
            
            self.user_cache = user
        return self.cleaned_data