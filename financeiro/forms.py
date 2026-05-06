from django import forms

from .models import ConfiguracaoFinanceira, Contribuicao


class ContribuicaoForm(forms.ModelForm):
    class Meta:
        model = Contribuicao
        fields = ["tipo", "valor", "descricao"]
        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 3}),
            "valor": forms.NumberInput(attrs={"min": "1.00", "step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    def clean_valor(self):
        valor = self.cleaned_data["valor"]
        if valor <= 0:
            raise forms.ValidationError("Informe um valor maior que zero.")
        return valor


class ConfiguracaoFinanceiraForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoFinanceira
        fields = [
            "ambiente",
            "mercado_pago_access_token",
            "mercado_pago_public_key",
            "mercado_pago_webhook_secret",
            "webhook_url",
        ]
        widgets = {
            "mercado_pago_access_token": forms.PasswordInput(),
            "mercado_pago_webhook_secret": forms.PasswordInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
        self.fields["mercado_pago_access_token"].required = False
        self.fields["mercado_pago_access_token"].help_text = (
            "Deixe em branco para manter o token atual."
        )
        self.fields["mercado_pago_webhook_secret"].required = False
        self.fields["mercado_pago_webhook_secret"].help_text = (
            "Deixe em branco para manter o segredo atual."
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.instance.pk:
            atual = ConfiguracaoFinanceira.objects.get(pk=self.instance.pk)
            if not self.cleaned_data.get("mercado_pago_access_token"):
                instance.mercado_pago_access_token = atual.mercado_pago_access_token
            if not self.cleaned_data.get("mercado_pago_webhook_secret"):
                instance.mercado_pago_webhook_secret = atual.mercado_pago_webhook_secret
        if commit:
            instance.save()
            self.save_m2m()
        return instance
