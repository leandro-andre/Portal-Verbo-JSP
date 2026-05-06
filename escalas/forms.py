from django import forms
from django.db.models import Q

from departamentos.models import DepartamentoMembro
from usuarios.permissions import usuario_pode_ser_escalado_departamento

from .models import CultoPadrao, Escala, EscalaItem, IndisponibilidadeMembro


class FormControlMixin:
    checkbox_class = "module-checkbox"

    def apply_control_classes(self):
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", self.checkbox_class)
            else:
                field.widget.attrs.setdefault("class", "form-control")


class IndisponibilidadeMembroForm(FormControlMixin, forms.ModelForm):
    class Meta:
        model = IndisponibilidadeMembro
        fields = ["data_inicio", "data_fim", "horario_inicio", "horario_fim", "motivo", "ativo"]
        widgets = {
            "data_inicio": forms.DateInput(attrs={"type": "date"}),
            "data_fim": forms.DateInput(attrs={"type": "date"}),
            "horario_inicio": forms.TimeInput(attrs={"type": "time"}),
            "horario_fim": forms.TimeInput(attrs={"type": "time"}),
            "motivo": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_control_classes()


class CultoPadraoForm(FormControlMixin, forms.ModelForm):
    class Meta:
        model = CultoPadrao
        fields = ["nome", "dia_semana", "horario", "ativo", "observacoes"]
        widgets = {
            "horario": forms.TimeInput(attrs={"type": "time"}),
            "observacoes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_control_classes()


class GerarEscalasMesForm(FormControlMixin, forms.Form):
    departamento = forms.ModelChoiceField(queryset=None)
    ano = forms.IntegerField(min_value=2000, max_value=2100)
    mes = forms.IntegerField(min_value=1, max_value=12)
    cultos_padrao = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, departamentos_queryset=None, cultos_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["departamento"].queryset = departamentos_queryset
        self.fields["cultos_padrao"].queryset = cultos_queryset
        self.fields["cultos_padrao"].widget.attrs.setdefault("class", "module-checklist")
        self.apply_control_classes()


class EscalaForm(FormControlMixin, forms.ModelForm):
    class Meta:
        model = Escala
        fields = ["departamento", "culto_padrao", "titulo", "data", "horario", "observacoes", "ativa"]
        widgets = {
            "data": forms.DateInput(attrs={"type": "date"}),
            "horario": forms.TimeInput(attrs={"type": "time"}),
            "observacoes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, departamentos_queryset=None, cultos_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["departamento"].queryset = departamentos_queryset
        self.fields["culto_padrao"].queryset = cultos_queryset
        self.fields["culto_padrao"].required = False
        # Permite criar escalas a partir de culto padrão sem exigir título manual.
        self.fields["titulo"].required = False
        self.apply_control_classes()

    def clean(self):
        cleaned_data = super().clean()
        culto_padrao = cleaned_data.get("culto_padrao")
        if culto_padrao:
            cleaned_data["horario"] = culto_padrao.horario
            titulo = (cleaned_data.get("titulo") or "").strip()
            if not titulo:
                cleaned_data["titulo"] = culto_padrao.nome
        return cleaned_data


class EscalaItemForm(FormControlMixin, forms.ModelForm):
    class Meta:
        model = EscalaItem
        fields = ["participacao", "funcao", "confirmado", "observacoes"]
        widgets = {
            "observacoes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, escala=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.escala = escala
        if escala is not None:
            self.fields["participacao"].queryset = (
                DepartamentoMembro.objects.filter(
                    Q(membro__status_eclesiastico="membro")
                    | Q(membro__eh_pastor=True)
                    | Q(membro__is_superuser=True),
                    departamento=escala.departamento,
                    ativo=True,
                )
                .select_related("membro")
                .order_by("membro__first_name", "membro__last_name", "membro__username")
            )
        self.apply_control_classes()

    def clean_participacao(self):
        participacao = self.cleaned_data["participacao"]
        if not usuario_pode_ser_escalado_departamento(participacao.membro):
            raise forms.ValidationError("A pessoa escalada precisa estar qualificada como membro.")
        return participacao

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.escala is not None:
            instance.escala = self.escala
        if commit:
            instance.save()
        return instance
