from django.contrib import admin

from .models import Departamento, DepartamentoMembro


class DepartamentoMembroInline(admin.TabularInline):
    model = DepartamentoMembro
    extra = 0
    autocomplete_fields = ("membro",)
    fields = ("membro", "papel", "ativo", "data_entrada")

@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ("nome", "codigo", "ativo", "total_membros_ativos", "criado_em")
    list_filter = ("ativo",)
    readonly_fields = ("codigo",)
    search_fields = ("nome", "codigo", "descricao")
    inlines = [DepartamentoMembroInline]

    @admin.display(description="Membros ativos")
    def total_membros_ativos(self, obj):
        return obj.participacoes.filter(ativo=True).count()


@admin.register(DepartamentoMembro)
class DepartamentoMembroAdmin(admin.ModelAdmin):
    list_display = ("membro", "departamento", "papel", "ativo", "data_entrada")
    list_filter = ("papel", "ativo", "departamento")
    search_fields = (
        "membro__username",
        "membro__first_name",
        "membro__last_name",
        "membro__email",
        "departamento__nome",
    )
    autocomplete_fields = ("membro", "departamento")
