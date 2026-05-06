from django.contrib import messages
from django.db.models import Count, Prefetch, Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import DepartamentoForm, DepartamentoMembroForm
from .models import Departamento, DepartamentoMembro
from .permissions import (
    DepartmentCreatorRequiredMixin,
    DepartmentLeaderRequiredMixin,
    DepartmentMemberRequiredMixin,
    get_departamentos_do_usuario,
    get_departamentos_gerenciaveis,
    usuario_pode_acessar_departamentos,
    usuario_pode_criar_departamentos,
)


class DepartamentoListView(DepartmentMemberRequiredMixin, ListView):
    model = Departamento
    template_name = "departamentos/lista.html"
    context_object_name = "departamentos"

    def test_func(self):
        return usuario_pode_acessar_departamentos(self.request.user)

    def get_queryset(self):
        query = (self.request.GET.get("q") or "").strip()
        status = (self.request.GET.get("status") or "").strip()
        if usuario_pode_criar_departamentos(self.request.user):
            base_queryset = Departamento.objects.all()
        else:
            base_queryset = get_departamentos_do_usuario(self.request.user)

        queryset = (
            base_queryset.annotate(
                total_membros_ativos_count=Count(
                    "participacoes",
                    filter=Q(participacoes__ativo=True),
                    distinct=True,
                )
            )
            .prefetch_related(
                Prefetch(
                    "participacoes",
                    queryset=DepartamentoMembro.objects.select_related("membro").order_by(
                        "papel", "membro__first_name", "membro__username"
                    ),
                )
            )
            .order_by("nome")
        )

        if query:
            queryset = queryset.filter(nome__icontains=query)

        if status == "ativos":
            queryset = queryset.filter(ativo=True)
        elif status == "inativos":
            queryset = queryset.filter(ativo=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "departamentos",
                "search_query": (self.request.GET.get("q") or "").strip(),
                "status_filter": (self.request.GET.get("status") or "").strip(),
                "total_departamentos": self.object_list.count(),
                "can_create_departamentos": usuario_pode_criar_departamentos(self.request.user),
                "departamentos_gerenciaveis_ids": set(
                    get_departamentos_gerenciaveis(self.request.user).values_list("id", flat=True)
                ),
            }
        )
        return context


class DepartamentoCreateView(DepartmentCreatorRequiredMixin, CreateView):
    model = Departamento
    form_class = DepartamentoForm
    template_name = "departamentos/form.html"
    success_url = reverse_lazy("usuarios:departamentos:lista")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "departamentos",
                "page_title": "Novo departamento",
                "page_eyebrow": "Departamentos",
                "page_text": "Crie um novo departamento para organizar equipes, liderancas e futuras escalas.",
                "submit_label": "Criar departamento",
            }
        )
        return context

    def form_valid(self, form):
        messages.success(self.request, "Departamento criado com sucesso.")
        return super().form_valid(form)


class DepartamentoUpdateView(DepartmentLeaderRequiredMixin, UpdateView):
    model = Departamento
    form_class = DepartamentoForm
    template_name = "departamentos/form.html"

    def get_success_url(self):
        return reverse("usuarios:departamentos:lista")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "departamentos",
                "page_title": f"Editar {self.object.nome}",
                "page_eyebrow": "Departamentos",
                "page_text": "Atualize as informacoes principais do departamento sem depender do admin bruto.",
                "submit_label": "Salvar alteracoes",
            }
        )
        return context

    def form_valid(self, form):
        messages.success(self.request, "Departamento atualizado com sucesso.")
        return super().form_valid(form)


class DepartamentoMembrosView(DepartmentLeaderRequiredMixin, DetailView):
    model = Departamento
    template_name = "departamentos/membros.html"
    context_object_name = "departamento"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        editar_id = self.request.GET.get("editar")
        participacao = None
        if editar_id:
            participacao = self._get_participacao_or_none(editar_id)

        form = kwargs.get("form")
        if form is None:
            form = DepartamentoMembroForm(instance=participacao, departamento=self.object)

        participacoes = self.object.participacoes.select_related("membro").order_by(
            "-ativo",
            "papel",
            "membro__first_name",
            "membro__last_name",
            "membro__username",
        )

        context.update(
            {
                "active_section": "departamentos",
                "form": form,
                "participacoes": participacoes,
                "editing_participacao": participacao,
                "membros_ativos_count": participacoes.filter(ativo=True).count(),
                "membros_inativos_count": participacoes.filter(ativo=False).count(),
                "lider_principal": self.object.lider_principal,
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        participacao = None
        participacao_id = request.POST.get("participacao_id")
        if participacao_id:
            participacao = get_object_or_404(
                DepartamentoMembro,
                pk=participacao_id,
                departamento=self.object,
            )

        form = DepartamentoMembroForm(
            request.POST,
            instance=participacao,
            departamento=self.object,
        )

        if form.is_valid():
            vinculo = form.save(commit=False)
            vinculo.departamento = self.object
            vinculo.save()
            if participacao:
                messages.success(request, "Vinculo atualizado com sucesso.")
            else:
                messages.success(request, "Membro vinculado ao departamento com sucesso.")
            return HttpResponseRedirect(self.get_success_url())

        return self.render_to_response(self.get_context_data(form=form, object=self.object))

    def get_success_url(self):
        return reverse("usuarios:departamentos:membros", args=[self.object.pk])

    def _get_participacao_or_none(self, participacao_id):
        try:
            return DepartamentoMembro.objects.select_related("membro").get(
                pk=participacao_id,
                departamento=self.object,
            )
        except (DepartamentoMembro.DoesNotExist, ValueError):
            return None


class DepartamentoMembroStatusView(DepartmentLeaderRequiredMixin, View):
    def post(self, request, pk, participacao_id):
        departamento = get_object_or_404(Departamento, pk=pk)
        participacao = get_object_or_404(
            DepartamentoMembro,
            pk=participacao_id,
            departamento=departamento,
        )
        participacao.ativo = not participacao.ativo
        participacao.save(update_fields=["ativo"])

        if participacao.ativo:
            messages.success(request, "Vinculo reativado com sucesso.")
        else:
            messages.success(request, "Vinculo desativado com sucesso.")

        return HttpResponseRedirect(reverse("usuarios:departamentos:membros", args=[departamento.pk]))
