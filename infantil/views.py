from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import (
    AulaSalaForm,
    ChamadaResponsavelForm,
    CriancaForm,
    CriancaReviewForm,
    MinhaCriancaForm,
    SalaInfantilForm,
    SalaMembroForm,
)
from .models import AulaSala, ChamadaResponsavel, Crianca, SalaInfantil, SalaMembro
from .permissions import (
    CadastroCriancaResponsavelEditRequiredMixin,
    CadastroCriancaReviewRequiredMixin,
    InfantilAccessRequiredMixin,
    SalaChildrenManageRequiredMixin,
    SalaChildrenViewRequiredMixin,
    SalaCallsManageRequiredMixin,
    SalaCreatorRequiredMixin,
    SalaEditRequiredMixin,
    SalaLessonsManageRequiredMixin,
    SalaLessonsViewRequiredMixin,
    SalaTeamManageRequiredMixin,
    SalaTeamViewRequiredMixin,
    get_salas_do_usuario,
    get_salas_lideradas,
    usuario_pode_acessar_minhas_criancas,
    usuario_pode_criar_salas_infantis,
    usuario_pode_criar_chamada_responsavel,
    usuario_pode_cancelar_chamada,
    usuario_pode_editar_sala,
    usuario_pode_gerenciar_aulas,
    usuario_pode_gerenciar_criancas,
    usuario_pode_gerenciar_equipe_sala,
    usuario_pode_resolver_chamada,
    usuario_pode_reenviar_chamada,
    usuario_pode_revisar_cadastros_infantis,
    usuario_pode_ver_chamadas_sala,
    usuario_pode_ver_crianca_do_responsavel,
    usuario_pode_ver_equipe_sala,
)
from .services import (
    atualizar_cadastro_responsavel,
    cadastrar_crianca_na_sala,
    cancelar_chamada,
    criar_cadastro_responsavel,
    criar_chamada_responsavel,
    get_chamadas_da_sala,
    reenviar_chamada,
    resolver_chamada,
    revisar_cadastro_infantil,
)


class MinhasCriancasListView(LoginRequiredMixin, ListView):
    model = Crianca
    template_name = "infantil/minhas_criancas.html"
    context_object_name = "criancas"

    def get_queryset(self):
        return Crianca.objects.do_responsavel(self.request.user).com_relacoes_basicas().recentes_primeiro()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = context["criancas"]
        context.update(
            {
                "active_section": "minhas_criancas",
                "can_register_children": usuario_pode_acessar_minhas_criancas(self.request.user),
                "total_cadastros": queryset.count(),
                "total_pendentes": queryset.filter(status=Crianca.Status.PENDENTE).count(),
                "total_aprovados": queryset.filter(status=Crianca.Status.APROVADO).count(),
            }
        )
        return context


class MinhaCriancaCreateView(LoginRequiredMixin, CreateView):
    model = Crianca
    form_class = MinhaCriancaForm
    template_name = "infantil/minha_crianca_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request_user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        criar_cadastro_responsavel(form, self.request.user)
        messages.success(self.request, "Cadastro enviado com sucesso para revisao do Infantil.")
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("usuarios:infantil:minhas_criancas")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "minhas_criancas",
                "page_title": "Cadastrar crianca",
                "page_eyebrow": "Minhas criancas",
                "page_text": "Preencha os dados da crianca para envio ao Departamento Infantil. O cadastro entra como pendente ate a revisao da equipe.",
                "submit_label": "Enviar cadastro",
            }
        )
        return context


class MinhaCriancaUpdateView(CadastroCriancaResponsavelEditRequiredMixin, UpdateView):
    model = Crianca
    form_class = MinhaCriancaForm
    template_name = "infantil/minha_crianca_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request_user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse("usuarios:infantil:minhas_criancas")

    def form_valid(self, form):
        _, reenviado_para_revisao = atualizar_cadastro_responsavel(form, self.object)
        if reenviado_para_revisao:
            messages.success(
                self.request,
                "Cadastro atualizado e reenviado para nova revisao do Infantil.",
            )
        else:
            messages.success(self.request, "Cadastro da crianca atualizado com sucesso.")
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "minhas_criancas",
                "page_title": f"Editar {self.object.nome}",
                "page_eyebrow": "Minhas criancas",
                "page_text": "Atualize os dados enviados ao Infantil. Alteracoes pelo responsavel ficam disponiveis enquanto o cadastro estiver pendente ou recusado.",
                "submit_label": "Salvar cadastro",
            }
        )
        return context


class CadastrosInfantisListView(CadastroCriancaReviewRequiredMixin, ListView):
    model = Crianca
    template_name = "infantil/cadastros_lista.html"
    context_object_name = "criancas"

    def get_queryset(self):
        status = (self.request.GET.get("status") or "").strip()
        queryset = Crianca.objects.com_relacoes_basicas().order_by("status", "-criado_em")
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = Crianca.objects.all()
        context.update(
            {
                "active_section": "infantil",
                "status_filter": (self.request.GET.get("status") or "").strip(),
                "pendentes_count": queryset.pendentes().count(),
                "aprovados_count": queryset.aprovadas().count(),
                "recusados_count": queryset.recusadas().count(),
            }
        )
        return context


class CadastroInfantilReviewView(CadastroCriancaReviewRequiredMixin, UpdateView):
    model = Crianca
    form_class = CriancaReviewForm
    template_name = "infantil/cadastro_review_form.html"

    def get_success_url(self):
        return reverse("usuarios:infantil:cadastros_lista")

    def form_valid(self, form):
        revisar_cadastro_infantil(form)
        messages.success(self.request, "Cadastro infantil atualizado com sucesso.")
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "infantil",
                "page_title": f"Revisar cadastro: {self.object.nome}",
                "page_eyebrow": "Cadastros do Infantil",
                "page_text": "Revise os dados enviados pelo responsavel, aprove ou recuse o cadastro e vincule a crianca a sala adequada.",
                "submit_label": "Salvar revisao",
            }
        )
        return context


class SalaListView(InfantilAccessRequiredMixin, ListView):
    model = SalaInfantil
    template_name = "infantil/salas_lista.html"
    context_object_name = "salas"

    def get_queryset(self):
        query = (self.request.GET.get("q") or "").strip()
        status = (self.request.GET.get("status") or "").strip()

        if usuario_pode_criar_salas_infantis(self.request.user):
            base_queryset = SalaInfantil.objects.all()
        else:
            base_queryset = get_salas_do_usuario(self.request.user)

        queryset = (
            base_queryset.annotate(
                total_equipe_ativa_count=Count(
                    "equipe",
                    filter=Q(equipe__ativo=True),
                    distinct=True,
                ),
                total_criancas_ativas_count=Count(
                    "criancas",
                    filter=Q(criancas__ativo=True),
                    distinct=True,
                ),
            )
            .order_by("idade_minima", "idade_maxima", "nome")
        )

        if query:
            queryset = queryset.filter(nome__icontains=query)
        if status == "ativas":
            queryset = queryset.filter(ativa=True)
        elif status == "inativas":
            queryset = queryset.filter(ativa=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "infantil",
                "search_query": (self.request.GET.get("q") or "").strip(),
                "status_filter": (self.request.GET.get("status") or "").strip(),
                "can_create_salas": usuario_pode_criar_salas_infantis(self.request.user),
                "salas_lideradas_ids": set(
                    get_salas_lideradas(self.request.user).values_list("id", flat=True)
                ),
                "salas_editaveis_ids": {
                    sala.id
                    for sala in context["salas"]
                    if usuario_pode_editar_sala(self.request.user, sala)
                },
                "salas_equipe_visivel_ids": {
                    sala.id
                    for sala in context["salas"]
                    if usuario_pode_ver_equipe_sala(self.request.user, sala)
                },
                "salas_equipe_gerenciavel_ids": {
                    sala.id
                    for sala in context["salas"]
                    if usuario_pode_gerenciar_equipe_sala(self.request.user, sala)
                },
                "salas_criancas_gerenciaveis_ids": {
                    sala.id
                    for sala in context["salas"]
                    if usuario_pode_gerenciar_criancas(self.request.user, sala)
                },
                "salas_aulas_gerenciaveis_ids": {
                    sala.id
                    for sala in context["salas"]
                    if usuario_pode_gerenciar_aulas(self.request.user, sala)
                },
                "can_review_registrations": usuario_pode_revisar_cadastros_infantis(
                    self.request.user
                ),
                "salas_chamadas_ids": {
                    sala.id
                    for sala in context["salas"]
                    if usuario_pode_criar_chamada_responsavel(self.request.user, sala)
                },
            }
        )
        return context


class SalaCreateView(SalaCreatorRequiredMixin, CreateView):
    model = SalaInfantil
    form_class = SalaInfantilForm
    template_name = "infantil/sala_form.html"
    success_url = reverse_lazy("usuarios:infantil:sala_lista")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "infantil",
                "page_title": "Nova sala",
                "page_eyebrow": "Departamento Infantil",
                "page_text": "Crie uma nova sala para organizar equipe, criancas e licoes por faixa etaria.",
                "submit_label": "Criar sala",
            }
        )
        return context

    def form_valid(self, form):
        messages.success(self.request, "Sala criada com sucesso.")
        return super().form_valid(form)


class SalaUpdateView(SalaEditRequiredMixin, UpdateView):
    model = SalaInfantil
    form_class = SalaInfantilForm
    template_name = "infantil/sala_form.html"

    def get_success_url(self):
        return reverse("usuarios:infantil:sala_lista")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "infantil",
                "page_title": f"Editar {self.object.nome}",
                "page_eyebrow": "Departamento Infantil",
                "page_text": "Atualize a faixa etaria e os dados principais da sala.",
                "submit_label": "Salvar alteracoes",
            }
        )
        return context

    def form_valid(self, form):
        messages.success(self.request, "Sala atualizada com sucesso.")
        return super().form_valid(form)


class SalaEquipeView(SalaTeamViewRequiredMixin, DetailView):
    model = SalaInfantil
    template_name = "infantil/sala_equipe.html"
    context_object_name = "sala"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        editar_id = self.request.GET.get("editar")
        participacao = None
        if editar_id:
            participacao = self._get_participacao_or_none(editar_id)

        form = kwargs.get("form")
        if form is None:
            form = SalaMembroForm(instance=participacao, sala=self.object)

        equipe = self.object.equipe.select_related("membro").order_by(
            "-ativo",
            "papel",
            "membro__first_name",
            "membro__last_name",
            "membro__username",
        )

        context.update(
            {
                "active_section": "infantil",
                "form": form,
                "equipe": equipe,
                "editing_participacao": participacao,
                "total_ativos": equipe.filter(ativo=True).count(),
                "lideres_sala": equipe.filter(
                    ativo=True,
                    papel=SalaMembro.Papel.LIDER_SALA,
                ).count(),
                "can_manage_equipe": usuario_pode_gerenciar_equipe_sala(
                    self.request.user,
                    self.object,
                ),
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not usuario_pode_gerenciar_equipe_sala(request.user, self.object):
            return self.handle_no_permission()
        participacao = None
        participacao_id = request.POST.get("participacao_id")
        if participacao_id:
            participacao = get_object_or_404(
                SalaMembro,
                pk=participacao_id,
                sala=self.object,
            )

        form = SalaMembroForm(request.POST, instance=participacao, sala=self.object)
        if form.is_valid():
            vinculo = form.save(commit=False)
            vinculo.sala = self.object
            vinculo.save()
            if participacao:
                messages.success(request, "Equipe da sala atualizada com sucesso.")
            else:
                messages.success(request, "Membro adicionado a equipe da sala.")
            return HttpResponseRedirect(self.get_success_url())

        return self.render_to_response(self.get_context_data(form=form, object=self.object))

    def get_success_url(self):
        return reverse("usuarios:infantil:sala_equipe", args=[self.object.pk])

    def _get_participacao_or_none(self, participacao_id):
        try:
            return SalaMembro.objects.select_related("membro").get(
                pk=participacao_id,
                sala=self.object,
            )
        except (SalaMembro.DoesNotExist, ValueError):
            return None


class SalaMembroStatusView(SalaTeamManageRequiredMixin, View):
    def post(self, request, pk, participacao_id):
        sala = get_object_or_404(SalaInfantil, pk=pk)
        participacao = get_object_or_404(SalaMembro, pk=participacao_id, sala=sala)
        participacao.ativo = not participacao.ativo
        participacao.save(update_fields=["ativo"])

        if participacao.ativo:
            messages.success(request, "Vinculo da equipe reativado com sucesso.")
        else:
            messages.success(request, "Vinculo da equipe desativado com sucesso.")

        return HttpResponseRedirect(reverse("usuarios:infantil:sala_equipe", args=[sala.pk]))


class SalaChamadasView(SalaCallsManageRequiredMixin, DetailView):
    model = SalaInfantil
    template_name = "infantil/sala_chamadas.html"
    context_object_name = "sala"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = kwargs.get("form") or ChamadaResponsavelForm()
        chamadas_queryset = get_chamadas_da_sala(self.object)
        chamadas_ativas = chamadas_queryset.filter(
            status__in=(
                ChamadaResponsavel.Status.PENDENTE,
                ChamadaResponsavel.Status.EXIBIDO,
            )
        )
        historico = chamadas_queryset.exclude(
            status__in=(
                ChamadaResponsavel.Status.PENDENTE,
                ChamadaResponsavel.Status.EXIBIDO,
            )
        )[:10]

        context.update(
            {
                "active_section": "infantil",
                "form": form,
                "chamadas_ativas": chamadas_ativas,
                "historico_chamadas": historico,
                "total_pendentes": chamadas_ativas.filter(
                    status=ChamadaResponsavel.Status.PENDENTE
                ).count(),
                "total_exibidas": chamadas_ativas.filter(
                    status=ChamadaResponsavel.Status.EXIBIDO
                ).count(),
                "can_view_chamadas": usuario_pode_ver_chamadas_sala(
                    self.request.user,
                    self.object,
                ),
                "can_manage_status_chamadas": usuario_pode_ver_chamadas_sala(
                    self.request.user,
                    self.object,
                ),
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = ChamadaResponsavelForm(request.POST)
        if form.is_valid():
            criar_chamada_responsavel(form, self.object, request.user)
            messages.success(request, "Chamada enviada para a Midia com sucesso.")
            return HttpResponseRedirect(self.get_success_url())

        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse("usuarios:infantil:sala_chamadas", args=[self.object.pk])


class ChamadaResponsavelCancelView(View):
    def post(self, request, pk, chamada_id):
        sala = get_object_or_404(SalaInfantil, pk=pk)
        chamada = get_object_or_404(ChamadaResponsavel, pk=chamada_id, sala=sala)
        if not usuario_pode_cancelar_chamada(request.user, chamada):
            raise PermissionDenied

        cancelar_chamada(chamada)
        messages.success(request, "Chamada cancelada com sucesso.")
        return HttpResponseRedirect(reverse("usuarios:infantil:sala_chamadas", args=[sala.pk]))


class ChamadaResponsavelResolveView(View):
    def post(self, request, pk, chamada_id):
        sala = get_object_or_404(SalaInfantil, pk=pk)
        chamada = get_object_or_404(ChamadaResponsavel, pk=chamada_id, sala=sala)
        if not usuario_pode_resolver_chamada(request.user, chamada):
            raise PermissionDenied

        resolver_chamada(chamada)
        messages.success(request, "Chamada marcada como resolvida.")
        return HttpResponseRedirect(reverse("usuarios:infantil:sala_chamadas", args=[sala.pk]))


class ChamadaResponsavelReopenView(View):
    def post(self, request, pk, chamada_id):
        sala = get_object_or_404(SalaInfantil, pk=pk)
        chamada = get_object_or_404(ChamadaResponsavel, pk=chamada_id, sala=sala)
        if not usuario_pode_reenviar_chamada(request.user, chamada):
            raise PermissionDenied

        reenviar_chamada(chamada)
        messages.success(request, "Chamada reenviada para exibicao na Midia.")
        return HttpResponseRedirect(reverse("usuarios:infantil:sala_chamadas", args=[sala.pk]))


class SalaCriancasView(SalaChildrenViewRequiredMixin, DetailView):
    model = SalaInfantil
    template_name = "infantil/sala_criancas.html"
    context_object_name = "sala"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        criancas = Crianca.objects.da_sala(self.object).aprovadas().order_by("nome")
        context.update(
            {
                "active_section": "infantil",
                "criancas": criancas,
                "total_criancas": criancas.count(),
                "criancas_com_alerta": sum(1 for crianca in criancas if crianca.possui_alertas),
                "criancas_ativas": criancas.ativas().count(),
                "can_manage_criancas": usuario_pode_gerenciar_criancas(
                    self.request.user,
                    self.object,
                ),
            }
        )
        return context


class CriancaCreateView(SalaChildrenManageRequiredMixin, CreateView):
    model = Crianca
    form_class = CriancaForm
    template_name = "infantil/crianca_form.html"

    def get_permission_sala(self):
        return get_object_or_404(SalaInfantil, pk=self.kwargs["sala_pk"])

    def form_valid(self, form):
        cadastrar_crianca_na_sala(form, self.get_permission_sala())
        messages.success(self.request, "Crianca cadastrada com sucesso.")
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("usuarios:infantil:sala_criancas", args=[self.kwargs["sala_pk"]])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "infantil",
                "sala": self.get_permission_sala(),
                "page_title": "Nova crianca",
                "page_eyebrow": "Criancas da sala",
                "page_text": "Cadastre uma crianca e deixe as informacoes importantes bem organizadas para a equipe.",
                "submit_label": "Cadastrar crianca",
            }
        )
        return context


class CriancaUpdateView(SalaChildrenManageRequiredMixin, UpdateView):
    model = Crianca
    form_class = CriancaForm
    template_name = "infantil/crianca_form.html"

    def get_success_url(self):
        return reverse("usuarios:infantil:sala_criancas", args=[self.object.sala.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "infantil",
                "sala": self.object.sala,
                "page_title": f"Editar {self.object.nome}",
                "page_eyebrow": "Criancas da sala",
                "page_text": "Atualize rapidamente os dados da crianca, com destaque para alertas e cuidados.",
                "submit_label": "Salvar alteracoes",
            }
        )
        return context


class CriancaDetailView(SalaChildrenViewRequiredMixin, DetailView):
    model = Crianca
    template_name = "infantil/crianca_detail.html"
    context_object_name = "crianca"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "infantil",
                "sala": self.object.sala,
                "can_manage_criancas": usuario_pode_gerenciar_criancas(
                    self.request.user,
                    self.object.sala,
                ),
            }
        )
        return context


class SalaAulasView(SalaLessonsViewRequiredMixin, DetailView):
    model = SalaInfantil
    template_name = "infantil/sala_aulas.html"
    context_object_name = "sala"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        aulas = self.object.aulas.order_by("-data")
        context.update(
            {
                "active_section": "infantil",
                "aulas": aulas,
                "total_aulas": aulas.count(),
                "aulas_com_anexo": aulas.exclude(anexo_licao="").exclude(anexo_licao__isnull=True).count(),
                "can_manage_aulas": usuario_pode_gerenciar_aulas(
                    self.request.user,
                    self.object,
                ),
            }
        )
        return context


class AulaSalaCreateView(SalaLessonsManageRequiredMixin, CreateView):
    model = AulaSala
    form_class = AulaSalaForm
    template_name = "infantil/aula_form.html"

    def get_permission_sala(self):
        return get_object_or_404(SalaInfantil, pk=self.kwargs["sala_pk"])

    def form_valid(self, form):
        form.instance.sala = self.get_permission_sala()
        messages.success(self.request, "Aula cadastrada com sucesso.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("usuarios:infantil:sala_aulas", args=[self.kwargs["sala_pk"]])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "infantil",
                "sala": self.get_permission_sala(),
                "page_title": "Nova aula",
                "page_eyebrow": "Licoes da sala",
                "page_text": "Cadastre a licao da sala com conteudo em texto e, se precisar, um anexo para apoio da equipe.",
                "submit_label": "Cadastrar aula",
            }
        )
        return context


class AulaSalaUpdateView(SalaLessonsManageRequiredMixin, UpdateView):
    model = AulaSala
    form_class = AulaSalaForm
    template_name = "infantil/aula_form.html"

    def get_success_url(self):
        return reverse("usuarios:infantil:sala_aulas", args=[self.object.sala.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "infantil",
                "sala": self.object.sala,
                "page_title": f"Editar aula de {self.object.data.strftime('%d/%m/%Y')}",
                "page_eyebrow": "Licoes da sala",
                "page_text": "Atualize o tema, texto base, conteudo e anexo da licao.",
                "submit_label": "Salvar alteracoes",
            }
        )
        return context


class AulaSalaDetailView(SalaLessonsViewRequiredMixin, DetailView):
    model = AulaSala
    template_name = "infantil/aula_detail.html"
    context_object_name = "aula"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "infantil",
                "sala": self.object.sala,
                "can_manage_aulas": usuario_pode_gerenciar_aulas(
                    self.request.user,
                    self.object.sala,
                ),
            }
        )
        return context
