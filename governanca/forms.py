from django import forms

from .permissions import usuario_pode_editar_campo


class GovernedModelFormMixin(forms.ModelForm):
    request_user = None
    governed_model = None

    def __init__(self, *args, request_user=None, governed_model=None, **kwargs):
        self.request_user = request_user
        self.governed_model = governed_model or self._meta.model
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if not self.request_user:
            return cleaned_data

        for campo in self.changed_data:
            if not usuario_pode_editar_campo(
                self.request_user,
                self.governed_model,
                campo,
                obj=self.instance,
            ):
                self.add_error(campo, "Voce nao tem permissao para editar este campo.")

        return cleaned_data
