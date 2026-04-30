from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Usuario

class RegistroForm(UserCreationForm):
    """
    Formulário para auto-registro de novos membros.
    """
    first_name = forms.CharField(label="Nome", max_length=150, required=True)
    last_name = forms.CharField(label="Sobrenome", max_length=150, required=True)
    email = forms.EmailField(label="E-mail", required=True)
    telefone = forms.CharField(label="Telefone", max_length=20, required=False)

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = UserCreationForm.Meta.fields + ("first_name", "last_name", "email", "telefone")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

class LoginForm(AuthenticationForm):
    """
    Formulário de login customizado.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Seu nome de usuário'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Sua senha'
        })

class PerfilForm(forms.ModelForm):
    """
    Formulário para o usuário editar seus próprios dados.
    """
    class Meta:
        model = Usuario
        fields = ["first_name", "last_name", "email", "telefone", "data_nascimento", "foto"]
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'data_nascimento':
                self.fields[field].widget.attrs.update({'class': 'form-control'})
