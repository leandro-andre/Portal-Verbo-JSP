from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse

from governanca.admin_mixins import GovernedContentAdminMixin

from .models import ContatoMensagem, Lider, SiteConfig, SobrePage


@admin.register(SiteConfig)
class SiteConfigAdmin(GovernedContentAdminMixin, admin.ModelAdmin):
    list_display = ("nome_igreja", "atualizado_em")
    field_permission_visibility_mode = "hide"

    fieldsets = (
        ("Identidade Visual", {"fields": ("nome_igreja", "Logo_img")}),
        (
            "Heroes do site",
            {
                "fields": (
                    "hero_home",
                    "hero_sobre",
                    "hero_agenda",
                    "hero_noticias",
                    "hero_ao_vivo",
                    "hero_contato",
                )
            },
        ),
        ("Contatos", {"fields": ("telefone", "whatsapp", "email", "endereco")}),
        ("Redes Sociais", {"fields": ("instagram", "facebook")}),
        ("Institucional e Horarios", {"fields": ("texto_institucional", "horarios_cultos")}),
        ("Integracoes", {"fields": ("youtube_embed_url", "mapa_embed_url")}),
    )

    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

    def changelist_view(self, request, extra_context=None):
        """Redireciona a listagem direto pro form de edicao (singleton)."""
        obj, _ = self.model.objects.get_or_create(pk=1)
        return HttpResponseRedirect(
            reverse(
                f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
                args=[obj.pk],
            )
        )


class LiderInline(admin.TabularInline):
    model = Lider
    extra = 1
    fields = ("ordem", "nome", "cargo", "descricao", "foto")


@admin.register(ContatoMensagem)
class ContatoMensagemAdmin(admin.ModelAdmin):
    list_display = ("nome", "email", "assunto_resumido", "respondida", "criado_em")
    list_filter = ("respondida", "criado_em")
    search_fields = ("nome", "email", "assunto", "mensagem")
    readonly_fields = ("usuario", "nome", "email", "assunto", "mensagem", "criado_em", "atualizado_em")
    list_editable = ("respondida",)
    ordering = ("-criado_em",)

    fieldsets = (
        ("Contato", {"fields": ("usuario", "nome", "email", "assunto")}),
        ("Mensagem", {"fields": ("mensagem",)}),
        ("Atendimento", {"fields": ("respondida", "criado_em", "atualizado_em")}),
    )

    @admin.display(description="Assunto")
    def assunto_resumido(self, obj):
        return obj.assunto or "Sem assunto"

    def has_add_permission(self, request):
        return False


@admin.register(SobrePage)
class SobrePageAdmin(GovernedContentAdminMixin, admin.ModelAdmin):
    """
    Admin da pagina Sobre - singleton.
    Organizado em fieldsets para facil edicao.
    """

    fieldsets = (
        ("Banner / Hero", {"fields": ("banner_titulo", "banner_subtitulo")}),
        ("Nossa historia", {"fields": ("historia_titulo", "historia_texto")}),
        ("Missao, Visao e Valores", {"fields": ("missao", "visao", "valores")}),
    )

    inlines = [LiderInline]

    def has_add_permission(self, request):
        return not SobrePage.objects.exists() and super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        """Redireciona a listagem direto para o formulario de edicao."""
        obj = SobrePage.load()
        return redirect(f"../sobrepage/{obj.pk}/change/")
