from django import forms

from .models import FotoMinistro, Ministro


class StyledFormMixin:
    def _apply_default_classes(self):
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "module-checkbox")
            else:
                field.widget.attrs.setdefault("class", "form-control")


class MinistroInternoForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Ministro
        fields = [
            "usuario",
            "nome_completo",
            "nome_ministerial",
            "tipo",
            "status",
            "telefone_whatsapp",
            "email",
            "igreja_origem",
            "cidade",
            "estado",
            "pais",
            "biografia",
            "observacoes_internas",
            "foto_principal",
            "tipo_chave_pix",
            "chave_pix",
            "qr_code_pix",
            "favorecido_nome",
            "favorecido_documento",
            "banco",
            "observacoes_financeiras",
            "restricao_alimentar",
            "alergias",
            "preferencia_alimentacao",
            "observacoes_hospedagem",
            "observacoes_transporte",
            "necessidades_especiais",
            "ativo",
        ]
        widgets = {
            "biografia": forms.Textarea(attrs={"rows": 5}),
            "observacoes_internas": forms.Textarea(attrs={"rows": 4}),
            "observacoes_financeiras": forms.Textarea(attrs={"rows": 4}),
            "restricao_alimentar": forms.Textarea(attrs={"rows": 3}),
            "alergias": forms.Textarea(attrs={"rows": 3}),
            "preferencia_alimentacao": forms.Textarea(attrs={"rows": 3}),
            "observacoes_hospedagem": forms.Textarea(attrs={"rows": 3}),
            "observacoes_transporte": forms.Textarea(attrs={"rows": 3}),
            "necessidades_especiais": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_default_classes()
        self.fields["usuario"].required = False


class MinistroVisitanteForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Ministro
        fields = [
            "nome_completo",
            "nome_ministerial",
            "telefone_whatsapp",
            "email",
            "igreja_origem",
            "cidade",
            "estado",
            "pais",
            "biografia",
            "foto_principal",
            "tipo_chave_pix",
            "chave_pix",
            "qr_code_pix",
            "favorecido_nome",
            "favorecido_documento",
            "banco",
            "restricao_alimentar",
            "alergias",
            "preferencia_alimentacao",
            "observacoes_hospedagem",
            "observacoes_transporte",
            "necessidades_especiais",
        ]
        widgets = {
            "biografia": forms.Textarea(attrs={"rows": 5}),
            "restricao_alimentar": forms.Textarea(attrs={"rows": 3}),
            "alergias": forms.Textarea(attrs={"rows": 3}),
            "preferencia_alimentacao": forms.Textarea(attrs={"rows": 3}),
            "observacoes_hospedagem": forms.Textarea(attrs={"rows": 3}),
            "observacoes_transporte": forms.Textarea(attrs={"rows": 3}),
            "necessidades_especiais": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nome_completo"].required = True
        self.fields["email"].required = True
        self._apply_default_classes()


class FotoMinistroForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = FotoMinistro
        fields = ["imagem", "legenda", "destaque"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_default_classes()


class FotoMinistroInternoForm(FotoMinistroForm):
    class Meta:
        model = FotoMinistro
        fields = ["ministro", "imagem", "legenda", "destaque"]
