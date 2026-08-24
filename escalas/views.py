from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, ListView

from departamentos.permissions import (
    get_departamentos_gerenciaveis,
    usuario_pode_gerenciar_cultos_padrao,
)
from usuarios.permissions import usuario_tem_acesso_total_sistema

from .legacy_freeze import LegacySchedulingReadOnlyMixin, legacy_scheduling_read_only_response
from .models import CultoPadrao, Escala, IndisponibilidadeMembro
from .permissions import (
    CultoPadraoManagerRequiredMixin,
    EscalaLeaderRequiredMixin,
    EscalaManagerRequiredMixin,
    OwnIndisponibilidadeRequiredMixin,
    usuario_pode_acessar_escalas,
)
from .services import (
    get_itens_da_escala,
    get_indisponiveis_da_escala,
    listar_cultos_padrao,
    listar_escalas_gerenciaveis,
    listar_indisponibilidades_do_membro,
)


class EscalaQuerysetMixin(EscalaLeaderRequiredMixin):
    def get_manageable_departamentos(self):
        if not hasattr(self, "_manageable_departamentos"):
            self._manageable_departamentos = get_departamentos_gerenciaveis(self.request.user)
        return self._manageable_departamentos

    def get_queryset(self):
        queryset = Escala.objects.com_relacoes_basicas().com_itens_prefetch()
        if usuario_tem_acesso_total_sistema(self.request.user):
            return queryset
        return queryset.filter(departamento__in=self.get_manageable_departamentos())


class MinhasIndisponibilidadesListView(LoginRequiredMixin, ListView):
    model = IndisponibilidadeMembro
    template_name = "departamentos/minhas_indisponibilidades.html"
    context_object_name = "indisponibilidades"

    def get_queryset(self):
        return listar_indisponibilidades_do_membro(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "indisponibilidades",
                "total_indisponibilidades": self.object_list.count(),
                "ativas_count": self.object_list.filter(ativo=True).count(),
                "canceladas_count": self.object_list.filter(ativo=False).count(),
            }
        )
        return context


class IndisponibilidadeCreateView(LoginRequiredMixin, LegacySchedulingReadOnlyMixin, View):
    legacy_target_url = "/minhas-indisponibilidades"


class IndisponibilidadeUpdateView(OwnIndisponibilidadeRequiredMixin, LegacySchedulingReadOnlyMixin, View):
    legacy_target_url = "/minhas-indisponibilidades"


class IndisponibilidadeCancelView(OwnIndisponibilidadeRequiredMixin, View):
    def post(self, request, pk):
        return legacy_scheduling_read_only_response()


class CultoPadraoListView(CultoPadraoManagerRequiredMixin, ListView):
    model = CultoPadrao
    template_name = "departamentos/cultos_padrao_lista.html"
    context_object_name = "cultos"

    def get_queryset(self):
        query = (self.request.GET.get("q") or "").strip()
        status = (self.request.GET.get("status") or "").strip()
        return listar_cultos_padrao(query=query, status=status)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "escalas",
                "search_query": (self.request.GET.get("q") or "").strip(),
                "status_filter": (self.request.GET.get("status") or "").strip(),
            }
        )
        return context


class CultoPadraoCreateView(CultoPadraoManagerRequiredMixin, LegacySchedulingReadOnlyMixin, View):
    legacy_target_url = "/agenda-cultos/padroes"


class CultoPadraoUpdateView(CultoPadraoManagerRequiredMixin, LegacySchedulingReadOnlyMixin, View):
    legacy_target_url = "/agenda-cultos/padroes"


class CultoPadraoStatusView(CultoPadraoManagerRequiredMixin, View):
    def post(self, request, pk):
        return legacy_scheduling_read_only_response()


class EscalaListView(EscalaLeaderRequiredMixin, ListView):
    model = Escala
    template_name = "departamentos/escalas_lista.html"
    context_object_name = "escalas"

    def get_manageable_departamentos(self):
        if not hasattr(self, "_manageable_departamentos"):
            self._manageable_departamentos = get_departamentos_gerenciaveis(self.request.user)
        return self._manageable_departamentos

    def test_func(self):
        return usuario_pode_acessar_escalas(self.request.user)

    def get_queryset(self):
        query = (self.request.GET.get("q") or "").strip()
        status = (self.request.GET.get("status") or "").strip()
        departamento_id = (self.request.GET.get("departamento") or "").strip()
        return listar_escalas_gerenciaveis(
            user=self.request.user,
            departamentos_queryset=self.get_manageable_departamentos(),
            query=query,
            status=status,
            departamento_id=departamento_id,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        departamentos = self.get_manageable_departamentos().order_by("nome")
        context.update(
            {
                "active_section": "escalas",
                "search_query": (self.request.GET.get("q") or "").strip(),
                "status_filter": (self.request.GET.get("status") or "").strip(),
                "departamento_filter": (self.request.GET.get("departamento") or "").strip(),
                "departamentos_gerenciaveis": departamentos,
                "can_manage_cultos_padrao": usuario_pode_gerenciar_cultos_padrao(self.request.user),
            }
        )
        return context


class GerarEscalasMesView(EscalaManagerRequiredMixin, LegacySchedulingReadOnlyMixin, View):
    def test_func(self):
        return usuario_pode_acessar_escalas(self.request.user)


class EscalaCreateView(EscalaLeaderRequiredMixin, LegacySchedulingReadOnlyMixin, View):
    def test_func(self):
        return usuario_pode_acessar_escalas(self.request.user)


class EscalaUpdateView(EscalaQuerysetMixin, LegacySchedulingReadOnlyMixin, View):
    pass


class EscalaItensView(EscalaQuerysetMixin, DetailView):
    model = Escala
    template_name = "departamentos/escala_itens.html"
    context_object_name = "escala"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        itens = get_itens_da_escala(self.object)
        indisponiveis = get_indisponiveis_da_escala(self.object)

        context.update(
            {
                "active_section": "escalas",
                "itens": itens,
                "editing_item": None,
                "confirmados_count": itens.filter(confirmado=True).count(),
                "pendentes_count": itens.filter(confirmado=False).count(),
                "indisponiveis": indisponiveis,
                "legacy_read_only": True,
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        return legacy_scheduling_read_only_response()

    def get_success_url(self):
        return reverse("usuarios:departamentos:escala_itens", args=[self.object.pk])


class EscalaItemDeleteView(EscalaQuerysetMixin, View):
    def post(self, request, pk, item_id):
        return legacy_scheduling_read_only_response()
