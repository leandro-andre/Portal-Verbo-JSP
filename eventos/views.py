from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DetailView, FormView, ListView, UpdateView

from .forms import EventoGestaoForm, InscricaoEventoForm
from .models import Evento, InscricaoEvento
from .permissions import EventoManagerRequiredMixin, EventoTeamRequiredMixin, usuario_pode_operar_evento

import io
import qrcode


def agenda(request):
    """Eventos publicados, do mais proximo ao mais distante."""
    hoje = timezone.localdate()
    eventos = (
        Evento.objects
        .filter(publicado=True, data_inicio__gte=hoje)
        .order_by("data_inicio", "horario")
    )
    return render(request, "eventos/agenda.html", {"eventos": eventos})


class EventoInternoListView(EventoManagerRequiredMixin, ListView):
    model = Evento
    template_name = "eventos/interno_lista.html"
    context_object_name = "eventos"

    def get_queryset(self):
        query = (self.request.GET.get("q") or "").strip()
        status = (self.request.GET.get("status") or "").strip()
        categoria = (self.request.GET.get("categoria") or "").strip()
        data_inicio = (self.request.GET.get("data_inicio") or "").strip()
        data_fim = (self.request.GET.get("data_fim") or "").strip()

        queryset = Evento.objects.annotate(
            inscritos_count=Count(
                "inscricoes",
                filter=~Q(inscricoes__status=InscricaoEvento.Status.CANCELADO),
            ),
            presentes_count=Count(
                "inscricoes",
                filter=Q(inscricoes__status=InscricaoEvento.Status.PRESENTE),
            ),
        ).order_by("-data_inicio", "-horario", "-id")

        if query:
            queryset = queryset.filter(titulo__icontains=query)
        if status == "publicados":
            queryset = queryset.filter(publicado=True)
        elif status == "rascunhos":
            queryset = queryset.filter(publicado=False)
        elif status == "inscricoes_abertas":
            queryset = queryset.filter(inscricoes_abertas=True)
        elif status == "inscricoes_fechadas":
            queryset = queryset.filter(inscricoes_abertas=False)
        if categoria:
            queryset = queryset.filter(tipo=categoria)
        if data_inicio:
            queryset = queryset.filter(data_inicio__gte=data_inicio)
        if data_fim:
            queryset = queryset.filter(data_inicio__lte=data_fim)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "eventos",
                "search_query": (self.request.GET.get("q") or "").strip(),
                "status_filter": (self.request.GET.get("status") or "").strip(),
                "categoria_filter": (self.request.GET.get("categoria") or "").strip(),
                "data_inicio_filter": (self.request.GET.get("data_inicio") or "").strip(),
                "data_fim_filter": (self.request.GET.get("data_fim") or "").strip(),
                "categorias": Evento.TipoEvento.choices,
                "eventos_total": Evento.objects.count(),
                "eventos_publicados": Evento.objects.filter(publicado=True).count(),
            }
        )
        return context


class EventoCreateView(EventoManagerRequiredMixin, CreateView):
    model = Evento
    form_class = EventoGestaoForm
    template_name = "eventos/form.html"
    success_url = reverse_lazy("usuarios:eventos:interno_lista")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "eventos",
                "page_title": "Novo evento",
                "page_text": "Cadastre eventos especiais com inscricoes e check-in separados de cultos e escalas.",
                "submit_label": "Criar evento",
            }
        )
        return context

    def form_valid(self, form):
        messages.success(self.request, "Evento criado com sucesso.")
        return super().form_valid(form)


class EventoUpdateView(EventoManagerRequiredMixin, UpdateView):
    model = Evento
    form_class = EventoGestaoForm
    template_name = "eventos/form.html"

    def get_success_url(self):
        return reverse("usuarios:eventos:interno_detalhe", args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "eventos",
                "page_title": f"Editar evento: {self.object.titulo}",
                "page_text": "Atualize os dados do evento, publicacao, inscricoes e capacidade.",
                "submit_label": "Salvar evento",
            }
        )
        return context

    def form_valid(self, form):
        messages.success(self.request, "Evento atualizado com sucesso.")
        return super().form_valid(form)


class EventoDetailView(EventoManagerRequiredMixin, DetailView):
    model = Evento
    template_name = "eventos/interno_detalhe.html"
    context_object_name = "evento"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        evento = self.object
        total_inscritos = evento.total_inscritos
        total_presentes = evento.total_presentes
        percentual_presenca = (total_presentes / total_inscritos * 100) if total_inscritos else 0
        context.update(
            {
                "active_section": "eventos",
                "total_inscritos": total_inscritos,
                "total_presentes": total_presentes,
                "percentual_presenca": round(percentual_presenca, 1),
                "vagas_disponiveis": evento.vagas_disponiveis,
            }
        )
        return context


class EventoInscricaoListView(EventoTeamRequiredMixin, ListView):
    model = InscricaoEvento
    template_name = "eventos/inscricoes_lista.html"
    context_object_name = "inscricoes"

    def dispatch(self, request, *args, **kwargs):
        self.evento = get_object_or_404(Evento, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        query = (self.request.GET.get("q") or "").strip()
        status = (self.request.GET.get("status") or "").strip()
        queryset = self.evento.inscricoes.select_related("usuario").order_by("nome")
        if query:
            queryset = queryset.filter(
                Q(nome__icontains=query)
                | Q(telefone__icontains=query)
                | Q(email__icontains=query)
            )
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "eventos",
                "evento": self.evento,
                "search_query": (self.request.GET.get("q") or "").strip(),
                "status_filter": (self.request.GET.get("status") or "").strip(),
                "status_choices": InscricaoEvento.Status.choices,
            }
        )
        return context


class EventoCheckinView(EventoTeamRequiredMixin, ListView):
    model = InscricaoEvento
    template_name = "eventos/checkin.html"
    context_object_name = "inscricoes"

    def dispatch(self, request, *args, **kwargs):
        self.evento = get_object_or_404(Evento, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        query = (self.request.GET.get("q") or "").strip()
        queryset = self.evento.inscricoes.select_related("usuario").order_by("nome")
        if query:
            queryset = queryset.filter(
                Q(nome__icontains=query)
                | Q(telefone__icontains=query)
                | Q(email__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "eventos",
                "evento": self.evento,
                "search_query": (self.request.GET.get("q") or "").strip(),
            }
        )
        return context


class EventoMarcarPresencaView(EventoTeamRequiredMixin, View):
    def post(self, request, pk, inscricao_pk):
        evento = get_object_or_404(Evento, pk=pk)
        inscricao = get_object_or_404(evento.inscricoes, pk=inscricao_pk)
        if inscricao.status == InscricaoEvento.Status.PRESENTE or inscricao.checkin_realizado:
            messages.info(request, "Este participante ja teve o check-in registrado.")
        elif inscricao.status == InscricaoEvento.Status.CANCELADO:
            messages.error(request, "Nao e possivel fazer check-in de uma inscricao cancelada.")
        else:
            inscricao.registrar_checkin(por_usuario=request.user, quando=timezone.now())
            messages.success(request, "Presenca registrada com sucesso.")
        return HttpResponseRedirect(reverse("usuarios:eventos:checkin", args=[evento.pk]))


class EventoLeitorQRCodeView(EventoTeamRequiredMixin, View):
    template_name = "eventos/leitor_qr.html"

    def get(self, request, pk):
        evento = get_object_or_404(Evento, pk=pk)
        return render(request, self.template_name, {"evento": evento, "active_section": "eventos"})


class EventoCheckinApiView(EventoTeamRequiredMixin, View):
    def post(self, request, pk):
        evento = get_object_or_404(Evento, pk=pk)
        token = (request.POST.get("token") or "").strip()

        if not token:
            return JsonResponse(
                {"ok": False, "code": "qr_invalido", "message": "QR Code invalido."},
                status=400,
            )

        try:
            inscricao = InscricaoEvento.objects.select_related("evento").get(codigo_checkin=token)
        except InscricaoEvento.DoesNotExist:
            return JsonResponse(
                {"ok": False, "code": "nao_encontrada", "message": "Inscricao nao encontrada."},
                status=404,
            )

        if inscricao.evento_id != evento.id:
            return JsonResponse(
                {"ok": False, "code": "evento_diferente", "message": "QR Code invalido para este evento."},
                status=400,
            )

        if inscricao.status == InscricaoEvento.Status.CANCELADO:
            return JsonResponse(
                {"ok": False, "code": "invalida", "message": "Inscricao invalida."},
                status=400,
            )

        if inscricao.status == InscricaoEvento.Status.PRESENTE or inscricao.checkin_realizado:
            return JsonResponse(
                {
                    "ok": True,
                    "code": "ja_realizado",
                    "message": "Participante ja realizou check-in.",
                    "data": {
                        "nome": inscricao.nome,
                        "email": inscricao.email,
                        "telefone": inscricao.telefone,
                        "status": inscricao.status,
                        "checkin_em": inscricao.checkin_em.isoformat() if inscricao.checkin_em else None,
                    },
                }
            )

        inscricao.registrar_checkin(por_usuario=request.user, quando=timezone.now())
        return JsonResponse(
            {
                "ok": True,
                "code": "realizado",
                "message": "Check-in realizado com sucesso.",
                "data": {
                    "nome": inscricao.nome,
                    "email": inscricao.email,
                    "telefone": inscricao.telefone,
                    "status": inscricao.status,
                    "checkin_em": inscricao.checkin_em.isoformat() if inscricao.checkin_em else None,
                },
            }
        )


class CheckinPorTokenView(EventoTeamRequiredMixin, View):
    template_name = "eventos/checkin_token.html"

    def get_inscricao(self, codigo_checkin):
        try:
            return InscricaoEvento.objects.select_related("evento").get(codigo_checkin=codigo_checkin)
        except InscricaoEvento.DoesNotExist:
            return None

    def get(self, request, codigo_checkin):
        inscricao = self.get_inscricao(codigo_checkin)
        if not inscricao:
            messages.error(request, "Inscricao invalida.")
            return render(request, self.template_name, {"inscricao": None})
        return render(request, self.template_name, {"inscricao": inscricao})

    def post(self, request, codigo_checkin):
        inscricao = self.get_inscricao(codigo_checkin)
        if not inscricao:
            messages.error(request, "Inscricao invalida.")
            return render(request, self.template_name, {"inscricao": None})

        if inscricao.status == InscricaoEvento.Status.PRESENTE or inscricao.checkin_realizado:
            messages.info(request, "Inscricao ja fez check-in.")
            return HttpResponseRedirect(reverse("eventos:checkin_token", args=[inscricao.codigo_checkin]))

        if inscricao.status == InscricaoEvento.Status.CANCELADO:
            messages.error(request, "Inscricao invalida.")
            return HttpResponseRedirect(reverse("eventos:checkin_token", args=[inscricao.codigo_checkin]))

        inscricao.registrar_checkin(por_usuario=request.user, quando=timezone.now())
        messages.success(request, "Check-in realizado.")
        return HttpResponseRedirect(reverse("eventos:checkin_token", args=[inscricao.codigo_checkin]))


class MinhaInscricaoDetailView(LoginRequiredMixin, DetailView):
    model = InscricaoEvento
    template_name = "eventos/inscricao_detalhe.html"
    context_object_name = "inscricao"

    def get_queryset(self):
        return (
            InscricaoEvento.objects
            .select_related("evento")
            .filter(usuario=self.request.user)
        )


class InscricaoQRCodeView(LoginRequiredMixin, View):
    def get(self, request, pk):
        inscricao = get_object_or_404(
            InscricaoEvento.objects.select_related("evento", "usuario"),
            pk=pk,
        )
        if inscricao.usuario_id != request.user.id and not usuario_pode_operar_evento(request.user):
            raise PermissionDenied

        checkin_url = request.build_absolute_uri(
            reverse("eventos:checkin_token", args=[inscricao.codigo_checkin])
        )
        img = qrcode.make(checkin_url)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return HttpResponse(buf.getvalue(), content_type="image/png")


class EventoInscricaoCreateView(LoginRequiredMixin, FormView):
    form_class = InscricaoEventoForm
    template_name = "eventos/inscricao_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.evento = get_object_or_404(Evento, pk=kwargs["pk"], publicado=True)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["evento"] = self.evento
        kwargs["usuario"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"active_section": "minhas_inscricoes", "evento": self.evento})
        return context

    def form_valid(self, form):
        inscricao = form.save()
        messages.success(self.request, "Inscricao realizada com sucesso.")
        return HttpResponseRedirect(reverse("usuarios:eventos:minhas_inscricoes") + f"#inscricao-{inscricao.pk}")


class MinhasInscricoesView(LoginRequiredMixin, ListView):
    model = InscricaoEvento
    template_name = "eventos/minhas_inscricoes.html"
    context_object_name = "inscricoes"

    def get_queryset(self):
        return (
            InscricaoEvento.objects
            .select_related("evento")
            .filter(usuario=self.request.user)
            .order_by("-evento__data_inicio", "-criado_em")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_section"] = "minhas_inscricoes"
        return context


class CancelarMinhaInscricaoView(LoginRequiredMixin, View):
    def post(self, request, pk):
        inscricao = get_object_or_404(InscricaoEvento, pk=pk, usuario=request.user)
        if inscricao.status == InscricaoEvento.Status.PRESENTE:
            raise PermissionDenied
        inscricao.status = InscricaoEvento.Status.CANCELADO
        inscricao.save(update_fields=["status", "atualizado_em"])
        messages.success(request, "Inscricao cancelada com sucesso.")
        return HttpResponseRedirect(reverse("usuarios:eventos:minhas_inscricoes"))
