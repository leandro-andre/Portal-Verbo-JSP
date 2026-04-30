from django import forms
from django.core.exceptions import ValidationError

from .models import Evento, InscricaoEvento


class EventoGestaoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = [
            "titulo",
            "descricao",
            "imagem",
            "data_inicio",
            "data_fim",
            "horario",
            "local",
            "tipo",
            "capacidade_maxima",
            "publicado",
            "inscricoes_abertas",
            "destaque_home",
        ]
        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 5}),
            "data_inicio": forms.DateInput(attrs={"type": "date"}),
            "data_fim": forms.DateInput(attrs={"type": "date"}),
            "horario": forms.TimeInput(attrs={"type": "time"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "module-checkbox")
            else:
                field.widget.attrs.setdefault("class", "form-control")


class InscricaoEventoForm(forms.ModelForm):
    class Meta:
        model = InscricaoEvento
        fields = ["nome", "telefone", "email"]

    def __init__(self, *args, evento=None, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.evento = evento
        self.usuario = usuario
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

        if usuario and getattr(usuario, "is_authenticated", False):
            full_name = usuario.get_full_name()
            self.fields["nome"].initial = full_name or usuario.username
            self.fields["telefone"].initial = getattr(usuario, "telefone", "")
            self.fields["email"].initial = usuario.email

    def clean_email(self):
        return (self.cleaned_data["email"] or "").strip().lower()

    def clean(self):
        cleaned_data = super().clean()
        if not self.evento:
            return cleaned_data

        if not self.evento.inscricoes_permitidas():
            raise ValidationError("As inscricoes para este evento nao estao disponiveis.")

        email = cleaned_data.get("email")
        if email and self.evento.inscricoes.filter(email__iexact=email).exists():
            raise ValidationError("Ja existe uma inscricao para este e-mail neste evento.")

        if (
            self.usuario
            and getattr(self.usuario, "is_authenticated", False)
            and self.evento.inscricoes.filter(usuario=self.usuario).exists()
        ):
            raise ValidationError("Voce ja esta inscrito neste evento.")

        return cleaned_data

    def save(self, commit=True):
        inscricao = super().save(commit=False)
        inscricao.evento = self.evento
        if self.usuario and getattr(self.usuario, "is_authenticated", False):
            inscricao.usuario = self.usuario
        if commit:
            inscricao.save()
        return inscricao
