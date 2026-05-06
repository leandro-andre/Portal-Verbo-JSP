from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.dateparse import parse_date
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from core.models import SiteConfig, SobrePage
from eventos.models import Evento
from governanca.permissions import (
    usuario_pode_acessar_painel_midia,
    usuario_pode_acessar_painel_secretaria,
    usuario_pode_gerenciar_ao_vivo,
    usuario_pode_publicar_conteudo,
)
from infantil.models import ChamadaResponsavel
from infantil.permissions import (
    usuario_pode_marcar_chamada_exibida,
    usuario_pode_operar_chamadas_na_midia,
    usuario_pode_resolver_chamada,
)
from infantil.services import (
    get_chamadas_exibidas_para_midia,
    get_chamadas_pendentes_para_midia,
    get_chamadas_pendentes_payload,
    marcar_chamada_como_exibida,
    resolver_chamada,
)
from noticias.models import Noticia

from .forms import (
    EventoInternoForm,
    LiderInlineFormSet,
    MidiaAoVivoForm,
    NoticiaInternaForm,
    SecretariaContatoForm,
    SecretariaSiteConfigForm,
    SobrePageForm,
)
from .services import (
    alternar_publicacao_evento,
    alternar_publicacao_noticia,
    atualizar_evento_publico,
    atualizar_site_config,
    atualizar_sobre_page,
    atualizar_transmissao_ao_vivo,
    atualizar_noticia_publica,
    criar_evento_publico,
    criar_noticia_publica,
)


class SecretariaRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return usuario_pode_acessar_painel_secretaria(self.request.user)


class MidiaRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return usuario_pode_acessar_painel_midia(self.request.user)


class GovernedFormRequestMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request_user"] = self.request.user
        return kwargs


class SingleSiteConfigObjectMixin:
    model = SiteConfig

    def get_object(self, queryset=None):
        obj, _ = SiteConfig.objects.get_or_create(pk=1)
        return obj


class SingleSobrePageObjectMixin:
    model = SobrePage

    def get_object(self, queryset=None):
        return SobrePage.load()


class SecretariaDashboardView(SecretariaRequiredMixin, TemplateView):
    template_name = "conteudo_interno/secretaria_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "secretaria",
                "site_config": SiteConfig.objects.first(),
                "sobre_page": SobrePage.load(),
                "eventos_total": Evento.objects.count(),
                "eventos_publicados": Evento.objects.filter(publicado=True).count(),
                "noticias_total": Noticia.objects.count(),
                "noticias_publicadas": Noticia.objects.filter(publicado=True).count(),
                "visitantes_total": get_user_model().objects.filter(
                    status_eclesiastico=get_user_model().StatusEclesiastico.VISITANTE,
                    is_active=True,
                ).count(),
                "membros_total": get_user_model().objects.filter(
                    status_eclesiastico=get_user_model().StatusEclesiastico.MEMBRO,
                    is_active=True,
                ).count(),
            }
        )
        return context


class SecretariaQualificacaoPessoasView(SecretariaRequiredMixin, ListView):
    template_name = "conteudo_interno/qualificacao_pessoas.html"
    context_object_name = "pessoas"
    paginate_by = 30

    def get_queryset(self):
        user_model = get_user_model()
        query = (self.request.GET.get("q") or "").strip()
        status = (self.request.GET.get("status") or user_model.StatusEclesiastico.VISITANTE).strip()

        queryset = user_model.objects.filter(is_active=True).select_related("qualificado_por").order_by(
            "first_name",
            "last_name",
            "username",
        )
        if status:
            queryset = queryset.filter(status_eclesiastico=status)
        if query:
            queryset = queryset.filter(
                Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(username__icontains=query)
                | Q(email__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        user_model = get_user_model()
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "secretaria",
                "search_query": (self.request.GET.get("q") or "").strip(),
                "status_filter": (self.request.GET.get("status") or user_model.StatusEclesiastico.VISITANTE).strip(),
                "status_choices": user_model.StatusEclesiastico.choices,
                "visitantes_total": user_model.objects.filter(
                    status_eclesiastico=user_model.StatusEclesiastico.VISITANTE,
                    is_active=True,
                ).count(),
                "membros_total": user_model.objects.filter(
                    status_eclesiastico=user_model.StatusEclesiastico.MEMBRO,
                    is_active=True,
                ).count(),
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        user_model = get_user_model()
        pessoa = get_object_or_404(user_model, pk=request.POST.get("usuario_id"), is_active=True)
        acao = request.POST.get("acao")
        data_conclusao = parse_date(request.POST.get("discipulado_concluido_em") or "")

        if acao == "marcar_discipulado":
            pessoa.discipulado_concluido = True
            if data_conclusao:
                pessoa.discipulado_concluido_em = data_conclusao
            pessoa.save(update_fields=["discipulado_concluido", "discipulado_concluido_em"])
            messages.success(request, "Discipulado marcado como concluido.")
        elif acao == "qualificar":
            if not pessoa.discipulado_concluido and not data_conclusao:
                messages.error(request, "Informe a conclusao do discipulado antes de qualificar como membro.")
                return HttpResponseRedirect(self._get_redirect_url())

            pessoa.qualificar_como_membro(request.user, discipulado_concluido_em=data_conclusao)
            pessoa.save(
                update_fields=[
                    "status_eclesiastico",
                    "discipulado_concluido",
                    "discipulado_concluido_em",
                    "qualificado_por",
                    "qualificado_em",
                ]
            )
            messages.success(request, "Pessoa qualificada como membro.")
        else:
            messages.error(request, "Acao de qualificacao invalida.")

        return HttpResponseRedirect(self._get_redirect_url())

    def _get_redirect_url(self):
        query = self.request.META.get("QUERY_STRING")
        url = reverse("usuarios:conteudo:secretaria_qualificacao")
        return f"{url}?{query}" if query else url


class SecretariaSiteConfigUpdateView(
    SecretariaRequiredMixin,
    GovernedFormRequestMixin,
    SingleSiteConfigObjectMixin,
    UpdateView,
):
    form_class = SecretariaSiteConfigForm
    template_name = "conteudo_interno/site_config_form.html"
    success_url = reverse_lazy("usuarios:conteudo:secretaria_dashboard")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "secretaria",
                "page_title": "Configuracoes do site",
                "page_text": "Edite identidade, contatos, redes sociais, heroes das paginas publicas, horarios e integracoes do portal.",
                "submit_label": "Salvar configuracoes",
            }
        )
        return context

    def form_valid(self, form):
        self.object = atualizar_site_config(form, self.request.user)
        messages.success(self.request, "Configuracoes do site atualizadas com sucesso.")
        return HttpResponseRedirect(self.get_success_url())


class SecretariaContatoUpdateView(
    SecretariaRequiredMixin,
    GovernedFormRequestMixin,
    SingleSiteConfigObjectMixin,
    UpdateView,
):
    form_class = SecretariaContatoForm
    template_name = "conteudo_interno/contato_form.html"
    success_url = reverse_lazy("usuarios:conteudo:secretaria_dashboard")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "secretaria",
                "page_title": "Contato e localizacao",
                "page_text": "Atualize os dados exibidos na pagina de contato, no rodape e no mapa do site.",
                "submit_label": "Salvar dados de contato",
            }
        )
        return context

    def form_valid(self, form):
        self.object = atualizar_site_config(form, self.request.user)
        messages.success(self.request, "Dados de contato atualizados com sucesso.")
        return HttpResponseRedirect(self.get_success_url())


class SecretariaSobreUpdateView(
    SecretariaRequiredMixin,
    GovernedFormRequestMixin,
    SingleSobrePageObjectMixin,
    UpdateView,
):
    form_class = SobrePageForm
    template_name = "conteudo_interno/sobre_form.html"
    success_url = reverse_lazy("usuarios:conteudo:secretaria_dashboard")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["lider_formset"] = LiderInlineFormSet(
                self.request.POST,
                self.request.FILES,
                instance=self.object,
                prefix="lideres",
            )
        else:
            context["lider_formset"] = LiderInlineFormSet(
                instance=self.object,
                prefix="lideres",
            )
        context.update(
            {
                "active_section": "secretaria",
                "page_title": "Pagina Sobre",
                "page_text": "Edite historia, missao, visao, valores e a lideranca exibida no site. Contato e horarios ficam centralizados nas configuracoes do site.",
                "submit_label": "Salvar pagina Sobre",
            }
        )
        return context

    def form_valid(self, form):
        context = self.get_context_data(form=form)
        lider_formset = context["lider_formset"]
        if not lider_formset.is_valid():
            return self.render_to_response(context)

        self.object = atualizar_sobre_page(form, lider_formset, self.request.user)
        messages.success(self.request, "Pagina Sobre atualizada com sucesso.")
        return HttpResponseRedirect(self.get_success_url())


class SecretariaEventoListView(SecretariaRequiredMixin, ListView):
    model = Evento
    template_name = "conteudo_interno/eventos_lista.html"
    context_object_name = "eventos"

    def get_queryset(self):
        query = (self.request.GET.get("q") or "").strip()
        status = (self.request.GET.get("status") or "").strip()

        queryset = Evento.objects.all().order_by("-data_inicio", "-horario", "-id")
        if query:
            queryset = queryset.filter(titulo__icontains=query)
        if status == "publicados":
            queryset = queryset.filter(publicado=True)
        elif status == "rascunhos":
            queryset = queryset.filter(publicado=False)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "secretaria",
                "search_query": (self.request.GET.get("q") or "").strip(),
                "status_filter": (self.request.GET.get("status") or "").strip(),
                "eventos_publicados": Evento.objects.filter(publicado=True).count(),
                "eventos_total": Evento.objects.count(),
            }
        )
        return context


class SecretariaEventoCreateView(
    SecretariaRequiredMixin,
    GovernedFormRequestMixin,
    CreateView,
):
    model = Evento
    form_class = EventoInternoForm
    template_name = "conteudo_interno/evento_form.html"
    success_url = reverse_lazy("usuarios:conteudo:secretaria_eventos")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "secretaria",
                "page_title": "Novo evento",
                "page_text": "Cadastre e publique eventos da agenda publica da igreja.",
                "submit_label": "Criar evento",
            }
        )
        return context

    def form_valid(self, form):
        self.object = criar_evento_publico(form, self.request.user)
        messages.success(self.request, "Evento criado com sucesso.")
        return HttpResponseRedirect(self.get_success_url())


class SecretariaEventoUpdateView(
    SecretariaRequiredMixin,
    GovernedFormRequestMixin,
    UpdateView,
):
    model = Evento
    form_class = EventoInternoForm
    template_name = "conteudo_interno/evento_form.html"
    success_url = reverse_lazy("usuarios:conteudo:secretaria_eventos")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "secretaria",
                "page_title": f"Editar evento: {self.object.titulo}",
                "page_text": "Atualize os dados do evento e controle a exibicao publica pelo status de publicacao.",
                "submit_label": "Salvar evento",
            }
        )
        return context

    def form_valid(self, form):
        self.object = atualizar_evento_publico(form, self.request.user)
        messages.success(self.request, "Evento atualizado com sucesso.")
        return HttpResponseRedirect(self.get_success_url())


class SecretariaEventoPublishToggleView(SecretariaRequiredMixin, View):
    def post(self, request, pk):
        evento = get_object_or_404(Evento, pk=pk)
        if not usuario_pode_publicar_conteudo(request.user, Evento):
            raise PermissionDenied

        evento = alternar_publicacao_evento(evento, request.user)
        messages.success(
            request,
            "Evento publicado com sucesso." if evento.publicado else "Evento despublicado com sucesso.",
        )
        return HttpResponseRedirect(reverse("usuarios:conteudo:secretaria_eventos"))

class SecretariaNoticiaListView(SecretariaRequiredMixin, ListView):
    model = Noticia
    template_name = "conteudo_interno/noticias_lista.html"
    context_object_name = "noticias"

    def get_queryset(self):
        query = (self.request.GET.get("q") or "").strip()
        status = (self.request.GET.get("status") or "").strip()

        queryset = Noticia.objects.all().order_by("-data_publicacao", "-criado_em")
        if query:
            queryset = queryset.filter(titulo__icontains=query)
        if status == "publicadas":
            queryset = queryset.filter(publicado=True)
        elif status == "rascunhos":
            queryset = queryset.filter(publicado=False)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "secretaria",
                "search_query": (self.request.GET.get("q") or "").strip(),
                "status_filter": (self.request.GET.get("status") or "").strip(),
                "noticias_publicadas": Noticia.objects.filter(publicado=True).count(),
                "noticias_total": Noticia.objects.count(),
            }
        )
        return context


class SecretariaNoticiaCreateView(
    SecretariaRequiredMixin,
    GovernedFormRequestMixin,
    CreateView,
):
    model = Noticia
    form_class = NoticiaInternaForm
    template_name = "conteudo_interno/noticia_form.html"
    success_url = reverse_lazy("usuarios:conteudo:secretaria_noticias")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "secretaria",
                "page_title": "Nova noticia",
                "page_text": "Crie publicacoes e controle a exibicao publica pelo status de publicacao.",
                "submit_label": "Criar noticia",
            }
        )
        return context

    def form_valid(self, form):
        self.object = criar_noticia_publica(form, self.request.user)
        messages.success(self.request, "Noticia criada com sucesso.")
        return HttpResponseRedirect(self.get_success_url())


class SecretariaNoticiaUpdateView(
    SecretariaRequiredMixin,
    GovernedFormRequestMixin,
    UpdateView,
):
    model = Noticia
    form_class = NoticiaInternaForm
    template_name = "conteudo_interno/noticia_form.html"
    success_url = reverse_lazy("usuarios:conteudo:secretaria_noticias")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "secretaria",
                "page_title": f"Editar noticia: {self.object.titulo}",
                "page_text": "Atualize titulo, resumo, conteudo e status publico da noticia.",
                "submit_label": "Salvar noticia",
            }
        )
        return context

    def form_valid(self, form):
        self.object = atualizar_noticia_publica(form, self.request.user)
        messages.success(self.request, "Noticia atualizada com sucesso.")
        return HttpResponseRedirect(self.get_success_url())


class SecretariaNoticiaPublishToggleView(SecretariaRequiredMixin, View):
    def post(self, request, pk):
        noticia = get_object_or_404(Noticia, pk=pk)
        if not usuario_pode_publicar_conteudo(request.user, Noticia):
            raise PermissionDenied

        noticia = alternar_publicacao_noticia(noticia, request.user)
        messages.success(
            request,
            "Noticia publicada com sucesso." if noticia.publicado else "Noticia despublicada com sucesso.",
        )
        return HttpResponseRedirect(reverse("usuarios:conteudo:secretaria_noticias"))

class MidiaAoVivoUpdateView(
    MidiaRequiredMixin,
    GovernedFormRequestMixin,
    SingleSiteConfigObjectMixin,
    UpdateView,
):
    form_class = MidiaAoVivoForm
    template_name = "conteudo_interno/midia_ao_vivo.html"
    success_url = reverse_lazy("usuarios:conteudo:midia_ao_vivo")

    def dispatch(self, request, *args, **kwargs):
        if not usuario_pode_gerenciar_ao_vivo(request.user):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "midia",
                "page_title": "Transmissao Ao Vivo",
                "page_text": "Atualize somente o link de transmissao ao vivo. O sistema valida o formato e mostra um preview quando houver video configurado.",
                "youtube_src": self.object.youtube_embed_url_normalized,
                "video_watch_url": self.object.youtube_watch_url,
                "link_configurado": bool(self.object.youtube_video_id),
                "chamadas_pendentes": get_chamadas_pendentes_para_midia(),
                "chamadas_exibidas": get_chamadas_exibidas_para_midia(),
                "chamadas_endpoint": reverse("usuarios:conteudo:midia_chamadas_pendentes"),
            }
        )
        return context

    def form_valid(self, form):
        self.object = atualizar_transmissao_ao_vivo(form, self.request.user)
        messages.success(self.request, "Transmissao ao vivo atualizada com sucesso.")
        return HttpResponseRedirect(self.get_success_url())


class MidiaChamadaStatusView(MidiaRequiredMixin, View):
    action = None

    def post(self, request, pk):
        if not usuario_pode_operar_chamadas_na_midia(request.user):
            raise PermissionDenied

        chamada = get_object_or_404(ChamadaResponsavel.objects.com_relacoes_basicas(), pk=pk)
        if self.action == "exibido":
            if not usuario_pode_marcar_chamada_exibida(request.user, chamada):
                raise PermissionDenied
            marcar_chamada_como_exibida(chamada)
            messages.success(request, "Chamada marcada como exibida.")
        elif self.action == "resolvido":
            if not usuario_pode_resolver_chamada(request.user, chamada):
                raise PermissionDenied
            resolver_chamada(chamada)
            messages.success(request, "Chamada marcada como resolvida.")
        else:
            raise PermissionDenied

        return HttpResponseRedirect(reverse("usuarios:conteudo:midia_ao_vivo"))


class MidiaChamadaExibidoView(MidiaChamadaStatusView):
    action = "exibido"


class MidiaChamadaResolvidoView(MidiaChamadaStatusView):
    action = "resolvido"


class MidiaChamadasPendentesJsonView(MidiaRequiredMixin, View):
    def get(self, request):
        if not usuario_pode_operar_chamadas_na_midia(request.user):
            raise PermissionDenied

        return JsonResponse({"chamadas": get_chamadas_pendentes_payload()})
