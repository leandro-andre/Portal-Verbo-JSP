from django.contrib import admin

from .models import AulaSala, ChamadaResponsavel, Crianca, SalaInfantil, SalaMembro


class SalaMembroInline(admin.TabularInline):
    model = SalaMembro
    extra = 0
    autocomplete_fields = ("membro",)
    fields = ("membro", "papel", "ativo")


class CriancaInline(admin.TabularInline):
    model = Crianca
    extra = 0
    fields = ("nome", "data_nascimento", "responsavel_nome", "responsavel_telefone", "ativo")
    show_change_link = True


@admin.register(SalaInfantil)
class SalaInfantilAdmin(admin.ModelAdmin):
    list_display = ("nome", "faixa_etaria_label", "ativa", "total_criancas_ativas", "total_equipe_ativa")
    list_filter = ("ativa",)
    search_fields = ("nome", "descricao")
    inlines = [SalaMembroInline, CriancaInline]

    @admin.display(description="Criancas ativas")
    def total_criancas_ativas(self, obj):
        return obj.criancas.filter(ativo=True).count()

    @admin.display(description="Equipe ativa")
    def total_equipe_ativa(self, obj):
        return obj.equipe.filter(ativo=True).count()


@admin.register(SalaMembro)
class SalaMembroAdmin(admin.ModelAdmin):
    list_display = ("membro", "sala", "papel", "ativo", "criado_em")
    list_filter = ("papel", "ativo", "sala")
    search_fields = (
        "membro__username",
        "membro__first_name",
        "membro__last_name",
        "membro__email",
        "sala__nome",
    )
    autocomplete_fields = ("membro", "sala")


@admin.register(Crianca)
class CriancaAdmin(admin.ModelAdmin):
    list_display = ("nome", "sala", "idade_atual", "responsavel_nome", "alertas_saude", "ativo")
    list_filter = ("ativo", "sala")
    search_fields = ("nome", "responsavel_nome", "responsavel_telefone")
    autocomplete_fields = ("sala",)

    @admin.display(description="Alertas")
    def alertas_saude(self, obj):
        return "Sim" if obj.possui_alertas else "Nao"


@admin.register(AulaSala)
class AulaSalaAdmin(admin.ModelAdmin):
    list_display = ("tema", "sala", "data", "possui_anexo", "criada_em")
    list_filter = ("sala", "data")
    search_fields = ("tema", "texto_base", "conteudo_licao")
    autocomplete_fields = ("sala",)

    @admin.display(description="Anexo")
    def possui_anexo(self, obj):
        return "Sim" if obj.anexo_licao else "Nao"


@admin.register(ChamadaResponsavel)
class ChamadaResponsavelAdmin(admin.ModelAdmin):
    list_display = ("sala", "numero_ficha", "status", "criado_por", "criado_em")
    list_filter = ("status", "sala")
    search_fields = ("numero_ficha", "observacao", "sala__nome")
    autocomplete_fields = ("sala", "criado_por")
