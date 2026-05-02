from django import forms
from django.core.exceptions import ValidationError

from .models import (
    CasaVerboNoLar,
    EscalaVerboNoLar,
    MaterialApoioVerboNoLar,
    ParticipanteVerboNoLar,
    RelatorioEncontroVerboNoLar,
)


class CasaVerboNoLarForm(forms.ModelForm):
    class Meta:
        model = CasaVerboNoLar
        fields = [
            "nome",
            "casal_responsavel",
            "anfitriao",
            "telefone_whatsapp",
            "endereco",
            "bairro",
            "ponto_referencia",
            "link_google_maps",
            "latitude",
            "longitude",
            "dia_padrao",
            "horario_padrao",
            "capacidade_aproximada",
            "ativo",
            "observacoes",
        ]
        widgets = {
            "horario_padrao": forms.TimeInput(attrs={"type": "time"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "module-checkbox")
            else:
                field.widget.attrs.setdefault("class", "form-control")


class ParticipanteVerboNoLarForm(forms.ModelForm):
    class Meta:
        model = ParticipanteVerboNoLar
        fields = ["tipo", "membro", "nome_visitante", "telefone", "ativo", "observacoes"]

    def __init__(self, *args, casa=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.casa = casa
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "module-checkbox")
            else:
                field.widget.attrs.setdefault("class", "form-control")

    def clean(self):
        cleaned_data = super().clean()
        if not self.casa and not self.instance.pk:
            return cleaned_data
        return cleaned_data

    def save(self, commit=True):
        participante = super().save(commit=False)
        if self.casa and not participante.pk:
            participante.casa = self.casa
        if commit:
            participante.full_clean()
            participante.save()
        return participante


class EscalaVerboNoLarForm(forms.ModelForm):
    class Meta:
        model = EscalaVerboNoLar
        fields = ["ministro", "data", "horario", "tema", "status", "observacoes"]
        widgets = {
            "data": forms.DateInput(attrs={"type": "date"}),
            "horario": forms.TimeInput(attrs={"type": "time"}),
        }

    def __init__(self, *args, casa=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.casa = casa
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "module-checkbox")
            else:
                field.widget.attrs.setdefault("class", "form-control")

    def save(self, commit=True):
        escala = super().save(commit=False)
        if self.casa and not escala.pk:
            escala.casa = self.casa
        if commit:
            escala.save()
        return escala


class MaterialApoioVerboNoLarForm(forms.ModelForm):
    class Meta:
        model = MaterialApoioVerboNoLar
        fields = ["titulo", "data", "texto_base", "conteudo", "anexo", "casa", "observacoes"]
        widgets = {
            "data": forms.DateInput(attrs={"type": "date"}),
            "conteudo": forms.Textarea(attrs={"rows": 8}),
            "observacoes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "module-checkbox")
            else:
                field.widget.attrs.setdefault("class", "form-control")


class RelatorioEncontroVerboNoLarForm(forms.ModelForm):
    class Meta:
        model = RelatorioEncontroVerboNoLar
        fields = [
            "data",
            "ministro",
            "tema",
            "quantidade_presentes",
            "quantidade_visitantes",
            "pedidos_oracao",
            "observacoes",
        ]
        widgets = {
            "data": forms.DateInput(attrs={"type": "date"}),
            "pedidos_oracao": forms.Textarea(attrs={"rows": 5}),
            "observacoes": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, casa=None, criado_por=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.casa = casa
        self.criado_por = criado_por
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "module-checkbox")
            else:
                field.widget.attrs.setdefault("class", "form-control")

    def save(self, commit=True):
        relatorio = super().save(commit=False)
        if self.casa and not relatorio.pk:
            relatorio.casa = self.casa
        if self.criado_por and not relatorio.pk:
            relatorio.criado_por = self.criado_por
        if commit:
            if not relatorio.casa_id:
                raise ValidationError("Casa nao informada.")
            if not relatorio.criado_por_id:
                raise ValidationError("Usuario criador nao informado.")
            relatorio.save()
        return relatorio

