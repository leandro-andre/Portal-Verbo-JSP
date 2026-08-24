from django.contrib import admin

from .models import CultoPadrao, Escala, EscalaItem, IndisponibilidadeMembro


class LegacySchedulingReadOnlyAdminMixin:
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_staff


class LegacySchedulingReadOnlyInlineMixin:
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class EscalaItemInline(LegacySchedulingReadOnlyInlineMixin, admin.TabularInline):
    model = EscalaItem
    extra = 0
    autocomplete_fields = ("participacao",)
    fields = ("participacao", "funcao", "confirmado")


@admin.register(CultoPadrao)
class CultoPadraoAdmin(LegacySchedulingReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("nome", "dia_semana", "horario", "ativo", "atualizado_em")
    list_filter = ("ativo", "dia_semana")
    search_fields = ("nome", "observacoes")


@admin.register(Escala)
class EscalaAdmin(LegacySchedulingReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("titulo", "departamento", "data", "horario", "ativa", "total_itens")
    list_filter = ("ativa", "departamento", "data")
    search_fields = ("titulo", "departamento__nome", "observacoes")
    autocomplete_fields = ("departamento", "culto_padrao")
    inlines = [EscalaItemInline]

    @admin.display(description="Itens")
    def total_itens(self, obj):
        return obj.itens.count()


@admin.register(EscalaItem)
class EscalaItemAdmin(LegacySchedulingReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("escala", "membro", "funcao", "confirmado")
    list_filter = ("confirmado", "escala__departamento")
    search_fields = (
        "escala__titulo",
        "funcao",
        "participacao__membro__username",
        "participacao__membro__first_name",
        "participacao__membro__last_name",
    )
    autocomplete_fields = ("escala", "participacao")

    @admin.display(description="Membro")
    def membro(self, obj):
        return obj.participacao.membro


@admin.register(IndisponibilidadeMembro)
class IndisponibilidadeMembroAdmin(LegacySchedulingReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("membro", "data_inicio", "data_fim", "horario_inicio", "horario_fim", "ativo")
    list_filter = ("ativo", "data_inicio")
    search_fields = (
        "membro__username",
        "membro__first_name",
        "membro__last_name",
        "motivo",
    )
    autocomplete_fields = ("membro",)
