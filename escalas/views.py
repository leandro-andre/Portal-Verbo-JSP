from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.views.generic.edit import FormView

from departamentos.models import Departamento
from departamentos.permissions import (
    get_departamentos_gerenciaveis,
    usuario_pode_gerenciar_cultos_padrao,
)
from usuarios.permissions import usuario_tem_acesso_total_sistema

from .forms import (
    CultoPadraoForm,
    EscalaForm,
    EscalaItemForm,
    GerarEscalasMesForm,
    IndisponibilidadeMembroForm,
)
from .legacy_freeze import LegacySchedulingReadOnlyMixin, legacy_scheduling_read_only_response
from .models import CultoPadrao, Escala, EscalaItem, IndisponibilidadeMembro
from .permissions import (
    CultoPadraoManagerRequiredMixin,
    EscalaLeaderRequiredMixin,
    EscalaManagerRequiredMixin,
    OwnIndisponibilidadeRequiredMixin,
    usuario_pode_acessar_escalas,
)
from .services import (
    alternar_status_culto_padrao,
    atualizar_culto_padrao,
    atualizar_escala,
    atualizar_indisponibilidade,
    cancelar_indisponibilidade,
    criar_culto_padrao,
    criar_escala,
    criar_indisponibilidade,
    gerar_escalas_do_mes,
    get_cultos_padrao_data,
    get_item_escala_or_none,
    get_itens_da_escala,
    get_indisponiveis_da_escala,
    listar_cultos_padrao,
    listar_escalas_gerenciaveis,
    listar_indisponibilidades_do_membro,
    remover_item_da_escala,
    salvar_item_escala,
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


class IndisponibilidadeCreateView(LoginRequiredMixin, LegacySchedulingReadOnlyMixin, CreateView):
    model = IndisponibilidadeMembro
    form_class = IndisponibilidadeMembroForm
    template_name = "departamentos/indisponibilidade_form.html"

    def form_valid(self, form):
        criar_indisponibilidade(form, self.request.user)
        messages.success(self.request, "Indisponibilidade cadastrada com sucesso.")
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("usuarios:departamentos:minhas_indisponibilidades")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "indisponibilidades",
                "page_title": "Nova indisponibilidade",
                "page_eyebrow": "Minhas indisponibilidades",
                "page_text": "Informe os dias e horarios em que voce nao podera servir para ajudar a lideranca a montar escalas melhores.",
                "submit_label": "Salvar indisponibilidade",
            }
        )
        return context


class IndisponibilidadeUpdateView(OwnIndisponibilidadeRequiredMixin, LegacySchedulingReadOnlyMixin, UpdateView):
    model = IndisponibilidadeMembro
    form_class = IndisponibilidadeMembroForm
    template_name = "departamentos/indisponibilidade_form.html"

    def get_success_url(self):
        return reverse("usuarios:departamentos:minhas_indisponibilidades")

    def form_valid(self, form):
        atualizar_indisponibilidade(form)
        messages.success(self.request, "Indisponibilidade atualizada com sucesso.")
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "indisponibilidades",
                "page_title": "Editar indisponibilidade",
                "page_eyebrow": "Minhas indisponibilidades",
                "page_text": "Ajuste o periodo informado sempre que sua agenda mudar.",
                "submit_label": "Salvar alteracoes",
            }
        )
        return context


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


class CultoPadraoCreateView(CultoPadraoManagerRequiredMixin, LegacySchedulingReadOnlyMixin, CreateView):
    model = CultoPadrao
    form_class = CultoPadraoForm
    template_name = "departamentos/culto_padrao_form.html"
    success_url = reverse_lazy("usuarios:departamentos:cultos_padrao_lista")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "escalas",
                "page_title": "Novo culto padrao",
                "page_eyebrow": "Cultos padrao",
                "page_text": "Cadastre os horarios fixos da igreja para acelerar a criacao de escalas e a geracao mensal.",
                "submit_label": "Criar culto padrao",
            }
        )
        return context

    def form_valid(self, form):
        criar_culto_padrao(form)
        messages.success(self.request, "Culto padrao criado com sucesso.")
        return HttpResponseRedirect(self.success_url)


class CultoPadraoUpdateView(CultoPadraoManagerRequiredMixin, LegacySchedulingReadOnlyMixin, UpdateView):
    model = CultoPadrao
    form_class = CultoPadraoForm
    template_name = "departamentos/culto_padrao_form.html"

    def get_success_url(self):
        return reverse("usuarios:departamentos:cultos_padrao_lista")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "escalas",
                "page_title": f"Editar {self.object.nome}",
                "page_eyebrow": "Cultos padrao",
                "page_text": "Ajuste dia da semana, horario e status do culto padrao para manter a base das escalas atualizada.",
                "submit_label": "Salvar alteracoes",
            }
        )
        return context

    def form_valid(self, form):
        atualizar_culto_padrao(form)
        messages.success(self.request, "Culto padrao atualizado com sucesso.")
        return HttpResponseRedirect(self.get_success_url())


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


class GerarEscalasMesView(EscalaManagerRequiredMixin, LegacySchedulingReadOnlyMixin, FormView):
    form_class = GerarEscalasMesForm
    template_name = "departamentos/gerar_escalas_mes.html"
    success_url = reverse_lazy("usuarios:departamentos:escala_lista")

    def get_manageable_departamentos(self):
        if not hasattr(self, "_manageable_departamentos"):
            self._manageable_departamentos = get_departamentos_gerenciaveis(self.request.user)
        return self._manageable_departamentos

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["departamentos_queryset"] = (
            Departamento.objects.all()
            if usuario_tem_acesso_total_sistema(self.request.user)
            else self.get_manageable_departamentos()
        )
        kwargs["cultos_queryset"] = CultoPadrao.objects.filter(ativo=True)
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial.setdefault("ano", self.request.GET.get("ano") or "")
        initial.setdefault("mes", self.request.GET.get("mes") or "")
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "escalas",
                "page_title": "Gerar escalas do mes",
                "page_eyebrow": "Escalas",
                "page_text": "Selecione o departamento, o mes e os cultos padrao ativos para criar a base mensal sem duplicar escalas existentes.",
                "submit_label": "Gerar escalas",
            }
        )
        return context

    def form_valid(self, form):
        resultado = gerar_escalas_do_mes(
            departamento=form.cleaned_data["departamento"],
            ano=form.cleaned_data["ano"],
            mes=form.cleaned_data["mes"],
            cultos_padroes=form.cleaned_data["cultos_padrao"],
        )
        messages.success(
            self.request,
            (
                f"Geracao concluida: {len(resultado['criadas'])} escala(s) criada(s) e "
                f"{len(resultado['ignoradas'])} ja existente(s) ignorada(s)."
            ),
        )
        return super().form_valid(form)


class EscalaCreateView(EscalaLeaderRequiredMixin, LegacySchedulingReadOnlyMixin, CreateView):
    model = Escala
    form_class = EscalaForm
    template_name = "departamentos/escala_form.html"
    success_url = reverse_lazy("usuarios:departamentos:escala_lista")

    def get_manageable_departamentos(self):
        if not hasattr(self, "_manageable_departamentos"):
            self._manageable_departamentos = get_departamentos_gerenciaveis(self.request.user)
        return self._manageable_departamentos

    def test_func(self):
        return usuario_pode_acessar_escalas(self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["departamentos_queryset"] = self.get_manageable_departamentos()
        kwargs["cultos_queryset"] = CultoPadrao.objects.filter(ativo=True)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "escalas",
                "page_title": "Nova escala",
                "page_eyebrow": "Escalas",
                "page_text": "Crie escalas apenas para os departamentos em que voce e lider, preparando a operacao do ministerio.",
                "submit_label": "Criar escala",
                "cultos_padrao_data": get_cultos_padrao_data(
                    CultoPadrao.objects.filter(ativo=True)
                ),
            }
        )
        return context

    def form_valid(self, form):
        criar_escala(form)
        messages.success(self.request, "Escala criada com sucesso.")
        return HttpResponseRedirect(self.success_url)


class EscalaUpdateView(EscalaQuerysetMixin, LegacySchedulingReadOnlyMixin, UpdateView):
    model = Escala
    form_class = EscalaForm
    template_name = "departamentos/escala_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["departamentos_queryset"] = self.get_manageable_departamentos()
        kwargs["cultos_queryset"] = CultoPadrao.objects.filter(ativo=True) | CultoPadrao.objects.filter(
            pk=getattr(self.object, "culto_padrao_id", None)
        )
        return kwargs

    def get_success_url(self):
        return reverse("usuarios:departamentos:escala_lista")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cultos_queryset = (
            CultoPadrao.objects.filter(ativo=True)
            | CultoPadrao.objects.filter(pk=getattr(self.object, "culto_padrao_id", None))
        ).distinct()
        context.update(
            {
                "active_section": "escalas",
                "page_title": f"Editar {self.object.titulo}",
                "page_eyebrow": "Escalas",
                "page_text": "Atualize data, horario e departamento da escala respeitando as permissoes de lideranca.",
                "submit_label": "Salvar alteracoes",
                "cultos_padrao_data": get_cultos_padrao_data(cultos_queryset),
            }
        )
        return context

    def form_valid(self, form):
        atualizar_escala(form)
        messages.success(self.request, "Escala atualizada com sucesso.")
        return HttpResponseRedirect(self.get_success_url())


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
