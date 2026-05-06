from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import Departamento, DepartamentoMembro
from usuarios.permissions import usuario_pode_ser_escalado_departamento


class DepartamentoForm(forms.ModelForm):
    class Meta:
        model = Departamento
        fields = ["nome", "codigo", "descricao", "ativo"]
        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 5, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["codigo"].required = False
        self.fields["codigo"].help_text = (
            "Use um codigo curto e estavel para regras internas. "
            "Se deixar em branco, ele sera gerado automaticamente."
        )
        for name, field in self.fields.items():
            if name == "ativo":
                field.widget.attrs["class"] = "module-checkbox"
            else:
                field.widget.attrs.setdefault("class", "form-control")

        self.fields["codigo"].widget.attrs.setdefault("placeholder", "ex.: secretaria")


class DepartamentoMembroForm(forms.ModelForm):
    class Meta:
        model = DepartamentoMembro
        fields = ["membro", "papel", "ativo", "data_entrada", "observacoes"]
        widgets = {
            "data_entrada": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "observacoes": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
        }

    def __init__(self, *args, departamento=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.departamento = departamento

        user_model = get_user_model()
        self.fields["membro"].queryset = user_model.objects.filter(
            Q(status_eclesiastico=user_model.StatusEclesiastico.MEMBRO)
            | Q(eh_pastor=True)
            | Q(is_superuser=True),
            is_active=True,
        ).order_by("first_name", "last_name", "username")
        self.fields["membro"].widget.attrs.setdefault("class", "form-control")
        self.fields["papel"].widget.attrs.setdefault("class", "form-control")
        self.fields["ativo"].widget.attrs.setdefault("class", "module-checkbox")
        self.fields["data_entrada"].widget.attrs.setdefault("class", "form-control")
        self.fields["observacoes"].widget.attrs.setdefault("class", "form-control")

    def clean(self):
        cleaned_data = super().clean()
        membro = cleaned_data.get("membro")
        ativo = cleaned_data.get("ativo")

        if membro and not usuario_pode_ser_escalado_departamento(membro):
            self.add_error(
                "membro",
                "A pessoa precisa estar qualificada como membro antes de servir em departamento.",
            )

        if self.departamento and membro and ativo:
            queryset = DepartamentoMembro.objects.filter(
                departamento=self.departamento,
                membro=membro,
                ativo=True,
            )
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                self.add_error(
                    "membro",
                    "Este membro ja possui um vinculo ativo com este departamento.",
                )

        return cleaned_data
