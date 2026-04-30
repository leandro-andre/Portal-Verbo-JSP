from django import forms

from .models import ContatoMensagem


class ContatoForm(forms.ModelForm):
    class Meta:
        model = ContatoMensagem
        fields = ["nome", "email", "assunto", "mensagem"]
        widgets = {
            "nome": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "Seu nome completo",
                    "autocomplete": "name",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "seuemail@exemplo.com",
                    "autocomplete": "email",
                }
            ),
            "assunto": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "Sobre o que deseja falar?",
                }
            ),
            "mensagem": forms.Textarea(
                attrs={
                    "class": "form-input form-textarea",
                    "placeholder": "Escreva sua mensagem aqui...",
                    "rows": 5,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assunto"].required = False

    def clean_nome(self):
        return " ".join(self.cleaned_data["nome"].split())
