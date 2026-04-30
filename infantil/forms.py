from django import forms
from django.contrib.auth import get_user_model

from .models import AulaSala, ChamadaResponsavel, Crianca, SalaInfantil, SalaMembro


SIM_NAO_CHOICES = (
    (True, "Sim"),
    (False, "Nao"),
)


class SalaInfantilForm(forms.ModelForm):
    class Meta:
        model = SalaInfantil
        fields = ["nome", "descricao", "idade_minima", "idade_maxima", "ativa"]
        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 5, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == "ativa":
                field.widget.attrs["class"] = "module-checkbox"
            else:
                field.widget.attrs.setdefault("class", "form-control")


class SalaMembroForm(forms.ModelForm):
    class Meta:
        model = SalaMembro
        fields = ["membro", "papel", "ativo", "observacoes"]
        widgets = {
            "observacoes": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
        }

    def __init__(self, *args, sala=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.sala = sala

        user_model = get_user_model()
        self.fields["membro"].queryset = user_model.objects.filter(is_active=True).order_by(
            "first_name", "last_name", "username"
        )
        self.fields["membro"].widget.attrs.setdefault("class", "form-control")
        self.fields["papel"].widget.attrs.setdefault("class", "form-control")
        self.fields["ativo"].widget.attrs.setdefault("class", "module-checkbox")
        self.fields["observacoes"].widget.attrs.setdefault("class", "form-control")

    def clean(self):
        cleaned_data = super().clean()
        membro = cleaned_data.get("membro")
        ativo = cleaned_data.get("ativo")

        if self.sala and membro and ativo:
            queryset = SalaMembro.objects.filter(
                sala=self.sala,
                membro=membro,
                ativo=True,
            )
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                self.add_error(
                    "membro",
                    "Este membro ja possui um vinculo ativo com esta sala.",
                )

        return cleaned_data


class CriancaForm(forms.ModelForm):
    class Meta:
        model = Crianca
        fields = [
            "nome",
            "data_nascimento",
            "sexo",
            "responsavel_nome",
            "responsavel_telefone",
            "responsavel_email",
            "observacoes_gerais",
            "alergias",
            "restricoes_alimentares",
            "necessidades_especiais",
            "pode_comer_lanche_igreja",
            "medicacao_ou_cuidado_especial",
            "observacao_para_professor",
            "ativo",
        ]
        widgets = {
            "data_nascimento": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "observacoes_gerais": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "alergias": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "restricoes_alimentares": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "necessidades_especiais": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "medicacao_ou_cuidado_especial": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "observacao_para_professor": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["pode_comer_lanche_igreja"].widget = forms.Select(
            choices=SIM_NAO_CHOICES,
            attrs={"class": "form-control"},
        )
        for name, field in self.fields.items():
            if name == "ativo":
                field.widget.attrs["class"] = "module-checkbox"
            else:
                field.widget.attrs.setdefault("class", "form-control")


class AulaSalaForm(forms.ModelForm):
    class Meta:
        model = AulaSala
        fields = ["data", "tema", "texto_base", "conteudo_licao", "anexo_licao", "observacoes"]
        widgets = {
            "data": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "conteudo_licao": forms.Textarea(attrs={"rows": 8, "class": "form-control"}),
            "observacoes": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class ChamadaResponsavelForm(forms.ModelForm):
    class Meta:
        model = ChamadaResponsavel
        fields = ["numero_ficha", "observacao"]
        widgets = {
            "observacao": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["numero_ficha"].widget.attrs.setdefault("class", "form-control")
        self.fields["observacao"].widget.attrs.setdefault("class", "form-control")


class MinhaCriancaForm(forms.ModelForm):
    class Meta:
        model = Crianca
        fields = [
            "nome",
            "data_nascimento",
            "sexo",
            "observacoes_gerais",
            "alergias",
            "restricoes_alimentares",
            "necessidades_especiais",
            "pode_comer_lanche_igreja",
            "medicacao_ou_cuidado_especial",
            "observacao_para_professor",
            "responsavel_nome",
            "responsavel_telefone",
            "responsavel_email",
        ]
        widgets = {
            "data_nascimento": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "observacoes_gerais": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "alergias": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "restricoes_alimentares": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "necessidades_especiais": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "medicacao_ou_cuidado_especial": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "observacao_para_professor": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }

    def __init__(self, *args, request_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request_user = request_user
        self.fields["pode_comer_lanche_igreja"].widget = forms.Select(
            choices=SIM_NAO_CHOICES,
            attrs={"class": "form-control"},
        )
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

        if request_user and not self.instance.pk:
            nome = request_user.get_full_name().strip() or request_user.username
            self.initial.setdefault("responsavel_nome", nome)
            self.initial.setdefault("responsavel_telefone", (request_user.telefone or "").strip())
            self.initial.setdefault("responsavel_email", (request_user.email or "").strip())


class CriancaReviewForm(forms.ModelForm):
    class Meta:
        model = Crianca
        fields = [
            "nome",
            "data_nascimento",
            "sexo",
            "status",
            "sala",
            "responsavel_nome",
            "responsavel_telefone",
            "responsavel_email",
            "observacoes_gerais",
            "alergias",
            "restricoes_alimentares",
            "necessidades_especiais",
            "pode_comer_lanche_igreja",
            "medicacao_ou_cuidado_especial",
            "observacao_para_professor",
            "ativo",
        ]
        widgets = {
            "data_nascimento": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "observacoes_gerais": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "alergias": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "restricoes_alimentares": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "necessidades_especiais": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "medicacao_ou_cuidado_especial": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "observacao_para_professor": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sala"].queryset = SalaInfantil.objects.filter(ativa=True).order_by(
            "idade_minima",
            "idade_maxima",
            "nome",
        )
        self.fields["sala"].required = False
        self.fields["pode_comer_lanche_igreja"].widget = forms.Select(
            choices=SIM_NAO_CHOICES,
            attrs={"class": "form-control"},
        )
        for name, field in self.fields.items():
            if name == "ativo":
                field.widget.attrs["class"] = "module-checkbox"
            else:
                field.widget.attrs.setdefault("class", "form-control")

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.status == Crianca.Status.APROVADO:
            instance.ativo = True
        elif instance.status in {
            Crianca.Status.PENDENTE,
            Crianca.Status.RECUSADO,
            Crianca.Status.INATIVO,
        }:
            instance.ativo = False

        if commit:
            instance.save()
        return instance
