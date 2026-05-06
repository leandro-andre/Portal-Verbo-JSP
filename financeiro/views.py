from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from .forms import ConfiguracaoFinanceiraForm, ContribuicaoForm
from .models import ConfiguracaoFinanceira, Contribuicao
from .permissions import usuario_pode_gerenciar_financeiro
from .services.mercado_pago import (
    MercadoPagoError,
    atualizar_contribuicao_por_pagamento,
    consultar_pagamento,
    criar_preferencia_pagamento,
    extrair_payment_id,
    testar_conexao,
    validar_assinatura_webhook,
)


class FinanceiroAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return usuario_pode_gerenciar_financeiro(self.request.user)


class ContribuicaoCreateView(LoginRequiredMixin, CreateView):
    model = Contribuicao
    form_class = ContribuicaoForm
    template_name = "financeiro/contribuicao_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_section"] = "contribuicoes"
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.usuario = self.request.user
        self.object.status = Contribuicao.Status.PENDENTE
        self.object.save()

        try:
            self.object = criar_preferencia_pagamento(self.object, self.request)
        except MercadoPagoError as exc:
            self.object.status = Contribuicao.Status.ERRO
            self.object.save(update_fields=["status", "atualizado_em"])
            messages.error(self.request, f"Nao foi possivel iniciar o pagamento: {exc}")
            return HttpResponseRedirect(reverse("financeiro:contribuir"))

        return redirect(self.object.link_pagamento)


class RetornoPagamentoView(LoginRequiredMixin, TemplateView):
    template_name = "financeiro/retorno.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payment_id = (
            self.request.GET.get("payment_id")
            or self.request.GET.get("collection_id")
        )
        contribuicao = None
        if payment_id and payment_id != "null":
            try:
                payment_data = consultar_pagamento(payment_id)
                contribuicao = atualizar_contribuicao_por_pagamento(payment_data)
            except MercadoPagoError as exc:
                messages.warning(self.request, f"Pagamento recebido para verificacao: {exc}")

        if not contribuicao:
            contribuicao = (
                Contribuicao.objects.filter(usuario=self.request.user)
                .order_by("-criado_em")
                .first()
            )

        context.update(
            {
                "active_section": "contribuicoes",
                "contribuicao": contribuicao,
            }
        )
        return context


class ConfiguracaoFinanceiraUpdateView(FinanceiroAdminRequiredMixin, UpdateView):
    form_class = ConfiguracaoFinanceiraForm
    model = ConfiguracaoFinanceira
    template_name = "financeiro/configuracao_form.html"
    success_url = reverse_lazy("usuarios:financeiro:configuracao")

    def get_object(self, queryset=None):
        return ConfiguracaoFinanceira.load()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_section"] = "financeiro"
        return context

    def form_valid(self, form):
        self.object = form.save()
        if self.request.POST.get("acao") == "testar_conexao":
            ok, mensagem = testar_conexao()
            if ok:
                messages.success(self.request, mensagem)
            else:
                messages.error(self.request, mensagem)
        else:
            messages.success(self.request, "Configuracoes financeiras atualizadas com sucesso.")
        return HttpResponseRedirect(self.get_success_url())


class ContribuicaoAdminListView(FinanceiroAdminRequiredMixin, ListView):
    model = Contribuicao
    template_name = "financeiro/contribuicoes_lista.html"
    context_object_name = "contribuicoes"
    paginate_by = 30

    def get_queryset(self):
        queryset = Contribuicao.objects.select_related("usuario").order_by("-criado_em", "-id")
        tipo = (self.request.GET.get("tipo") or "").strip()
        status = (self.request.GET.get("status") or "").strip()
        data_inicio = (self.request.GET.get("data_inicio") or "").strip()
        data_fim = (self.request.GET.get("data_fim") or "").strip()

        if tipo:
            queryset = queryset.filter(tipo=tipo)
        if status:
            queryset = queryset.filter(status=status)
        if data_inicio:
            queryset = queryset.filter(criado_em__date__gte=data_inicio)
        if data_fim:
            queryset = queryset.filter(criado_em__date__lte=data_fim)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.object_list
        context.update(
            {
                "active_section": "financeiro",
                "tipo_filter": (self.request.GET.get("tipo") or "").strip(),
                "status_filter": (self.request.GET.get("status") or "").strip(),
                "data_inicio": (self.request.GET.get("data_inicio") or "").strip(),
                "data_fim": (self.request.GET.get("data_fim") or "").strip(),
                "tipos": Contribuicao.Tipo.choices,
                "status_choices": Contribuicao.Status.choices,
                "total_filtrado": queryset.count(),
            }
        )
        return context


@method_decorator(csrf_exempt, name="dispatch")
class MercadoPagoWebhookView(View):
    def post(self, request):
        payment_id = extrair_payment_id(request)
        if not payment_id:
            return HttpResponse(status=200)

        valido, mensagem = validar_assinatura_webhook(request, payment_id)
        if not valido:
            return HttpResponse(mensagem, status=403)

        try:
            payment_data = consultar_pagamento(payment_id)
            atualizar_contribuicao_por_pagamento(payment_data)
        except MercadoPagoError:
            return HttpResponse(status=200)

        return HttpResponse(status=200)

    def get(self, request):
        return HttpResponse("Webhook financeiro ativo.", status=200)
