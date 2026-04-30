from django import forms
from django.forms import inlineformset_factory

from core.models import Lider, SiteConfig, SobrePage
from eventos.models import Evento
from governanca.forms import GovernedModelFormMixin
from noticias.models import Noticia


class _BaseStyledGovernedForm(GovernedModelFormMixin):
    def _apply_default_classes(self):
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "module-checkbox")
            else:
                field.widget.attrs.setdefault("class", "form-control")


class SecretariaSiteConfigForm(_BaseStyledGovernedForm):
    class Meta:
        model = SiteConfig
        fields = [
            "nome_igreja",
            "Logo_img",
            "hero_home",
            "hero_sobre",
            "hero_agenda",
            "hero_noticias",
            "hero_ao_vivo",
            "hero_contato",
            "telefone",
            "whatsapp",
            "email",
            "endereco",
            "instagram",
            "facebook",
            "texto_institucional",
            "horarios_cultos",
            "youtube_embed_url",
            "mapa_embed_url",
        ]
        widgets = {
            "texto_institucional": forms.Textarea(attrs={"rows": 4}),
            "horarios_cultos": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_default_classes()


class SecretariaContatoForm(_BaseStyledGovernedForm):
    class Meta:
        model = SiteConfig
        fields = [
            "telefone",
            "whatsapp",
            "email",
            "endereco",
            "horarios_cultos",
            "mapa_embed_url",
        ]
        widgets = {
            "horarios_cultos": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_default_classes()


class MidiaAoVivoForm(_BaseStyledGovernedForm):
    class Meta:
        model = SiteConfig
        fields = ["youtube_embed_url"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_default_classes()


class SobrePageForm(_BaseStyledGovernedForm):
    class Meta:
        model = SobrePage
        fields = [
            "banner_titulo",
            "banner_subtitulo",
            "historia_titulo",
            "historia_texto",
            "missao",
            "visao",
            "valores",
        ]
        widgets = {
            "banner_subtitulo": forms.Textarea(attrs={"rows": 3}),
            "historia_texto": forms.Textarea(attrs={"rows": 8}),
            "missao": forms.Textarea(attrs={"rows": 4}),
            "visao": forms.Textarea(attrs={"rows": 4}),
            "valores": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_default_classes()


class LiderForm(forms.ModelForm):
    class Meta:
        model = Lider
        fields = ["ordem", "nome", "cargo", "descricao", "foto"]
        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "form-control")


LiderInlineFormSet = inlineformset_factory(
    SobrePage,
    Lider,
    form=LiderForm,
    extra=1,
    can_delete=True,
)


class EventoInternoForm(_BaseStyledGovernedForm):
    class Meta:
        model = Evento
        fields = [
            "titulo",
            "descricao",
            "data",
            "horario",
            "local",
            "tipo",
            "imagem",
            "publicado",
            "destaque_home",
        ]
        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 5}),
            "data": forms.DateInput(attrs={"type": "date"}),
            "horario": forms.TimeInput(attrs={"type": "time"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_default_classes()


class NoticiaInternaForm(_BaseStyledGovernedForm):
    class Meta:
        model = Noticia
        fields = [
            "titulo",
            "slug",
            "resumo",
            "conteudo",
            "imagem",
            "publicado",
            "destaque_home",
            "data_publicacao",
        ]
        widgets = {
            "resumo": forms.Textarea(attrs={"rows": 4}),
            "conteudo": forms.Textarea(attrs={"rows": 10}),
            "data_publicacao": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False
        self._apply_default_classes()
