from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import (
    CasaVerboNoLarForm,
    EscalaVerboNoLarForm,
    MaterialApoioVerboNoLarForm,
    ParticipanteVerboNoLarForm,
    RelatorioEncontroVerboNoLarForm,
)
from .models import (
    CasaVerboNoLar,
    EscalaVerboNoLar,
    MaterialApoioVerboNoLar,
    ParticipanteVerboNoLar,
    RelatorioEncontroVerboNoLar,
)
from .permissions import (
    VerboNoLarAccessRequiredMixin,
    usuario_pode_gerenciar_verbo_no_lar,
    usuario_pode_operar_casa_verbo_no_lar,
)


class CasaScopedMixin:
    casa_pk_kwarg = "casa_pk"

    def get_casa(self):
        casa = get_object_or_404(CasaVerboNoLar, pk=self.kwargs[self.casa_pk_kwarg])
        if not usuario_pode_operar_casa_verbo_no_lar(self.request.user, casa):
            raise PermissionDenied
        return casa


class CasaListView(VerboNoLarAccessRequiredMixin, ListView):
    model = CasaVerboNoLar
    template_name = "verbo_no_lar/casas_lista.html"
    context_object_name = "casas"

    def get_queryset(self):
        query = (self.request.GET.get("q") or "").strip()
        ativo = (self.request.GET.get("ativo") or "").strip()

        qs = CasaVerboNoLar.objects.select_related("casal_responsavel", "anfitriao").order_by("-ativo", "nome")

        if not usuario_pode_gerenciar_verbo_no_lar(self.request.user):
            qs = qs.filter(Q(casal_responsavel=self.request.user) | Q(anfitriao=self.request.user))

        if query:
            qs = qs.filter(Q(nome__icontains=query) | Q(bairro__icontains=query))
        if ativo == "ativos":
            qs = qs.filter(ativo=True)
        elif ativo == "inativos":
            qs = qs.filter(ativo=False)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "verbo_no_lar",
                "search_query": (self.request.GET.get("q") or "").strip(),
                "ativo_filter": (self.request.GET.get("ativo") or "").strip(),
                "can_create": usuario_pode_gerenciar_verbo_no_lar(self.request.user),
            }
        )
        return context


class CasaCreateView(VerboNoLarAccessRequiredMixin, CreateView):
    model = CasaVerboNoLar
    form_class = CasaVerboNoLarForm
    template_name = "verbo_no_lar/casa_form.html"
    success_url = reverse_lazy("usuarios:verbo_no_lar:casa_lista")

    def dispatch(self, request, *args, **kwargs):
        if not usuario_pode_gerenciar_verbo_no_lar(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Casa cadastrada com sucesso.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "verbo_no_lar",
                "page_title": "Nova casa",
                "page_text": "Cadastre uma casa do Verbo no Lar com responsaveis, endereco e dia/horario padrao.",
                "submit_label": "Cadastrar casa",
            }
        )
        return context


class CasaUpdateView(VerboNoLarAccessRequiredMixin, UpdateView):
    model = CasaVerboNoLar
    form_class = CasaVerboNoLarForm
    template_name = "verbo_no_lar/casa_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not usuario_pode_operar_casa_verbo_no_lar(request.user, self.object):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("usuarios:verbo_no_lar:casa_detalhe", args=[self.object.pk])

    def form_valid(self, form):
        messages.success(self.request, "Casa atualizada com sucesso.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "verbo_no_lar",
                "page_title": f"Editar {self.object.nome}",
                "page_text": "Atualize endereco, responsaveis e configuracoes padrao do encontro.",
                "submit_label": "Salvar alteracoes",
            }
        )
        return context


class CasaDetailView(VerboNoLarAccessRequiredMixin, DetailView):
    model = CasaVerboNoLar
    template_name = "verbo_no_lar/casa_detalhe.html"
    context_object_name = "casa"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not usuario_pode_operar_casa_verbo_no_lar(request.user, self.object):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        casa = self.object
        context.update(
            {
                "active_section": "verbo_no_lar",
                "participantes_ativos": casa.participantes.filter(ativo=True).select_related("membro")[:10],
                "proximas_escalas": casa.escalas.select_related("ministro").order_by("-data")[:5],
                "ultimos_relatorios": casa.relatorios.select_related("ministro", "criado_por").order_by("-data")[:5],
                "can_edit": usuario_pode_operar_casa_verbo_no_lar(self.request.user, casa),
            }
        )
        return context


class ParticipanteListView(VerboNoLarAccessRequiredMixin, CasaScopedMixin, ListView):
    model = ParticipanteVerboNoLar
    template_name = "verbo_no_lar/participantes_lista.html"
    context_object_name = "participantes"

    def dispatch(self, request, *args, **kwargs):
        self.casa = self.get_casa()
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        query = (self.request.GET.get("q") or "").strip()
        qs = self.casa.participantes.select_related("membro").order_by("-ativo", "tipo", "nome_visitante")
        if query:
            qs = qs.filter(
                Q(nome_visitante__icontains=query)
                | Q(membro__first_name__icontains=query)
                | Q(membro__last_name__icontains=query)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "verbo_no_lar",
                "casa": self.casa,
                "search_query": (self.request.GET.get("q") or "").strip(),
            }
        )
        return context


class ParticipanteCreateView(VerboNoLarAccessRequiredMixin, CasaScopedMixin, CreateView):
    model = ParticipanteVerboNoLar
    form_class = ParticipanteVerboNoLarForm
    template_name = "verbo_no_lar/participante_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.casa = self.get_casa()
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["casa"] = self.casa
        return kwargs

    def get_success_url(self):
        return reverse("usuarios:verbo_no_lar:participantes", args=[self.casa.pk])

    def form_valid(self, form):
        messages.success(self.request, "Participante cadastrado com sucesso.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "verbo_no_lar",
                "casa": self.casa,
                "page_title": "Adicionar participante",
                "page_text": "Cadastre um membro (com conta) ou um visitante (sem conta).",
                "submit_label": "Salvar participante",
            }
        )
        return context


class ParticipanteUpdateView(VerboNoLarAccessRequiredMixin, UpdateView):
    model = ParticipanteVerboNoLar
    form_class = ParticipanteVerboNoLarForm
    template_name = "verbo_no_lar/participante_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.casa = self.object.casa
        if not usuario_pode_operar_casa_verbo_no_lar(request.user, self.casa):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["casa"] = self.casa
        return kwargs

    def get_success_url(self):
        return reverse("usuarios:verbo_no_lar:participantes", args=[self.casa.pk])

    def form_valid(self, form):
        messages.success(self.request, "Participante atualizado com sucesso.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "verbo_no_lar",
                "casa": self.casa,
                "page_title": "Editar participante",
                "page_text": "Atualize dados, tipo e status do participante.",
                "submit_label": "Salvar alteracoes",
            }
        )
        return context


class EscalaListView(VerboNoLarAccessRequiredMixin, CasaScopedMixin, ListView):
    model = EscalaVerboNoLar
    template_name = "verbo_no_lar/escalas_lista.html"
    context_object_name = "escalas"

    def dispatch(self, request, *args, **kwargs):
        self.casa = self.get_casa()
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.casa.escalas.select_related("ministro").order_by("-data", "-criado_em")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"active_section": "verbo_no_lar", "casa": self.casa})
        return context


class EscalaCreateView(VerboNoLarAccessRequiredMixin, CasaScopedMixin, CreateView):
    model = EscalaVerboNoLar
    form_class = EscalaVerboNoLarForm
    template_name = "verbo_no_lar/escala_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.casa = self.get_casa()
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["casa"] = self.casa
        return kwargs

    def get_success_url(self):
        return reverse("usuarios:verbo_no_lar:escalas", args=[self.casa.pk])

    def form_valid(self, form):
        messages.success(self.request, "Escala criada com sucesso.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "verbo_no_lar",
                "casa": self.casa,
                "page_title": "Nova escala",
                "page_text": "Programe o ministro e confirme status quando necessario.",
                "submit_label": "Salvar escala",
            }
        )
        return context


class EscalaUpdateView(VerboNoLarAccessRequiredMixin, UpdateView):
    model = EscalaVerboNoLar
    form_class = EscalaVerboNoLarForm
    template_name = "verbo_no_lar/escala_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.casa = self.object.casa
        if not usuario_pode_operar_casa_verbo_no_lar(request.user, self.casa):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["casa"] = self.casa
        return kwargs

    def get_success_url(self):
        return reverse("usuarios:verbo_no_lar:escalas", args=[self.casa.pk])

    def form_valid(self, form):
        messages.success(self.request, "Escala atualizada com sucesso.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "verbo_no_lar",
                "casa": self.casa,
                "page_title": "Editar escala",
                "page_text": "Atualize tema, horario e status.",
                "submit_label": "Salvar alteracoes",
            }
        )
        return context


class MaterialListView(VerboNoLarAccessRequiredMixin, ListView):
    model = MaterialApoioVerboNoLar
    template_name = "verbo_no_lar/materiais_lista.html"
    context_object_name = "materiais"

    def get_queryset(self):
        query = (self.request.GET.get("q") or "").strip()
        qs = MaterialApoioVerboNoLar.objects.select_related("casa").order_by("-data", "-criado_em")
        if query:
            qs = qs.filter(Q(titulo__icontains=query) | Q(texto_base__icontains=query) | Q(conteudo__icontains=query))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "verbo_no_lar",
                "search_query": (self.request.GET.get("q") or "").strip(),
                "can_create": usuario_pode_gerenciar_verbo_no_lar(self.request.user),
            }
        )
        return context


class MaterialCreateView(VerboNoLarAccessRequiredMixin, CreateView):
    model = MaterialApoioVerboNoLar
    form_class = MaterialApoioVerboNoLarForm
    template_name = "verbo_no_lar/material_form.html"
    success_url = reverse_lazy("usuarios:verbo_no_lar:materiais")

    def dispatch(self, request, *args, **kwargs):
        if not usuario_pode_gerenciar_verbo_no_lar(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Material cadastrado com sucesso.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "verbo_no_lar",
                "page_title": "Novo material",
                "page_text": "Cadastre material geral (todas as casas) ou vincule a uma casa especifica.",
                "submit_label": "Salvar material",
            }
        )
        return context


class MaterialUpdateView(VerboNoLarAccessRequiredMixin, UpdateView):
    model = MaterialApoioVerboNoLar
    form_class = MaterialApoioVerboNoLarForm
    template_name = "verbo_no_lar/material_form.html"

    def dispatch(self, request, *args, **kwargs):
        if not usuario_pode_gerenciar_verbo_no_lar(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("usuarios:verbo_no_lar:material_detalhe", args=[self.object.pk])

    def form_valid(self, form):
        messages.success(self.request, "Material atualizado com sucesso.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "verbo_no_lar",
                "page_title": "Editar material",
                "page_text": "Atualize titulo, texto base, conteudo e anexos.",
                "submit_label": "Salvar alteracoes",
            }
        )
        return context


class MaterialDetailView(VerboNoLarAccessRequiredMixin, DetailView):
    model = MaterialApoioVerboNoLar
    template_name = "verbo_no_lar/material_detalhe.html"
    context_object_name = "material"

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if usuario_pode_gerenciar_verbo_no_lar(request.user):
            return super().dispatch(request, *args, **kwargs)
        if obj.casa_id and not usuario_pode_operar_casa_verbo_no_lar(request.user, obj.casa):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"active_section": "verbo_no_lar"})
        return context


class RelatorioListView(VerboNoLarAccessRequiredMixin, CasaScopedMixin, ListView):
    model = RelatorioEncontroVerboNoLar
    template_name = "verbo_no_lar/relatorios_lista.html"
    context_object_name = "relatorios"

    def dispatch(self, request, *args, **kwargs):
        self.casa = self.get_casa()
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.casa.relatorios.select_related("ministro", "criado_por").order_by("-data", "-criado_em")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"active_section": "verbo_no_lar", "casa": self.casa})
        return context


class RelatorioCreateView(VerboNoLarAccessRequiredMixin, CasaScopedMixin, CreateView):
    model = RelatorioEncontroVerboNoLar
    form_class = RelatorioEncontroVerboNoLarForm
    template_name = "verbo_no_lar/relatorio_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.casa = self.get_casa()
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["casa"] = self.casa
        kwargs["criado_por"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse("usuarios:verbo_no_lar:relatorios", args=[self.casa.pk])

    def form_valid(self, form):
        messages.success(self.request, "Relatorio registrado com sucesso.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "verbo_no_lar",
                "casa": self.casa,
                "page_title": "Novo relatorio",
                "page_text": "Registre presentes, visitantes, pedidos de oracao e observacoes do encontro.",
                "submit_label": "Salvar relatorio",
            }
        )
        return context


class RelatorioDetailView(VerboNoLarAccessRequiredMixin, DetailView):
    model = RelatorioEncontroVerboNoLar
    template_name = "verbo_no_lar/relatorio_detalhe.html"
    context_object_name = "relatorio"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not usuario_pode_operar_casa_verbo_no_lar(request.user, self.object.casa):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"active_section": "verbo_no_lar", "casa": self.object.casa})
        return context
