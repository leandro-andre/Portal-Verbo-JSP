from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from .forms import FotoMinistroForm, FotoMinistroInternoForm, MinistroInternoForm, MinistroVisitanteForm
from .models import FotoMinistro, Ministro
from .permissions import MinistroManagerRequiredMixin


class MinistroListView(MinistroManagerRequiredMixin, ListView):
    model = Ministro
    template_name = "ministros/lista.html"
    context_object_name = "ministros"

    def get_queryset(self):
        query = (self.request.GET.get("q") or "").strip()
        tipo = (self.request.GET.get("tipo") or "").strip()
        status = (self.request.GET.get("status") or "").strip()
        ativo = (self.request.GET.get("ativo") or "").strip()

        queryset = Ministro.objects.all().order_by("nome_ministerial", "nome_completo")
        if query:
            queryset = queryset.filter(
                Q(nome_completo__icontains=query)
                | Q(nome_ministerial__icontains=query)
                | Q(igreja_origem__icontains=query)
                | Q(cidade__icontains=query)
            )
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        if status:
            queryset = queryset.filter(status=status)
        if ativo == "ativos":
            queryset = queryset.filter(ativo=True)
        elif ativo == "inativos":
            queryset = queryset.filter(ativo=False)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "ministros",
                "search_query": (self.request.GET.get("q") or "").strip(),
                "tipo_filter": (self.request.GET.get("tipo") or "").strip(),
                "status_filter": (self.request.GET.get("status") or "").strip(),
                "ativo_filter": (self.request.GET.get("ativo") or "").strip(),
                "tipo_choices": Ministro.Tipo.choices,
                "status_choices": Ministro.Status.choices,
                "total_ministros": Ministro.objects.count(),
                "pendentes_count": Ministro.objects.filter(status=Ministro.Status.PENDENTE).count(),
            }
        )
        return context


class MinistroCreateView(MinistroManagerRequiredMixin, CreateView):
    model = Ministro
    form_class = MinistroInternoForm
    template_name = "ministros/form.html"
    success_url = reverse_lazy("usuarios:ministros:lista")

    def form_valid(self, form):
        messages.success(self.request, "Ministro cadastrado com sucesso.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "ministros",
                "page_title": "Novo ministro",
                "page_text": "Cadastre dados ministeriais, financeiros e informacoes de cuidado em um unico registro.",
                "submit_label": "Cadastrar ministro",
            }
        )
        return context


class MinistroUpdateView(MinistroManagerRequiredMixin, UpdateView):
    model = Ministro
    form_class = MinistroInternoForm
    template_name = "ministros/form.html"

    def get_success_url(self):
        return reverse("usuarios:ministros:detalhe", args=[self.object.pk])

    def form_valid(self, form):
        messages.success(self.request, "Ministro atualizado com sucesso.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "ministros",
                "page_title": f"Editar {self.object.nome_exibicao}",
                "page_text": "Atualize os dados internos e revise informacoes enviadas pelo formulario externo.",
                "submit_label": "Salvar alteracoes",
            }
        )
        return context


class MinistroDetailView(MinistroManagerRequiredMixin, DetailView):
    model = Ministro
    template_name = "ministros/detalhe.html"
    context_object_name = "ministro"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "ministros",
                "fotos": self.object.fotos.all(),
                "formulario_url": self.request.build_absolute_uri(self.object.get_formulario_externo_url()),
            }
        )
        return context


class MinistroTokenRegenerateView(MinistroManagerRequiredMixin, View):
    def post(self, request, pk):
        ministro = get_object_or_404(Ministro, pk=pk)
        ministro.regenerar_token()
        messages.success(request, "Link do formulario externo regenerado com sucesso.")
        return HttpResponseRedirect(reverse("usuarios:ministros:detalhe", args=[ministro.pk]))


class MinistroGaleriaView(MinistroManagerRequiredMixin, DetailView):
    model = Ministro
    template_name = "ministros/galeria.html"
    context_object_name = "ministro"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "ministros",
                "form": kwargs.get("form") or FotoMinistroForm(),
                "fotos": self.object.fotos.all(),
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = FotoMinistroForm(request.POST, request.FILES)
        if form.is_valid():
            foto = form.save(commit=False)
            foto.ministro = self.object
            foto.save()
            messages.success(request, "Foto adicionada a galeria.")
            return HttpResponseRedirect(self.get_success_url())
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse("usuarios:ministros:galeria", args=[self.object.pk])


class FotoMinistroListView(MinistroManagerRequiredMixin, ListView):
    model = FotoMinistro
    template_name = "ministros/galeria_lista.html"
    context_object_name = "fotos"

    def get_queryset(self):
        query = (self.request.GET.get("q") or "").strip()
        queryset = FotoMinistro.objects.select_related("ministro").order_by(
            "ministro__nome_ministerial",
            "ministro__nome_completo",
            "-destaque",
            "-criado_em",
        )
        if query:
            queryset = queryset.filter(
                Q(ministro__nome_completo__icontains=query)
                | Q(ministro__nome_ministerial__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "ministros",
                "form": kwargs.get("form") or FotoMinistroInternoForm(),
                "search_query": (self.request.GET.get("q") or "").strip(),
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        form = FotoMinistroInternoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Foto adicionada a galeria.")
            return HttpResponseRedirect(reverse("usuarios:ministros:galeria_lista"))
        self.object_list = self.get_queryset()
        return self.render_to_response(self.get_context_data(form=form))


class FotoMinistroUpdateView(MinistroManagerRequiredMixin, UpdateView):
    model = FotoMinistro
    form_class = FotoMinistroForm
    template_name = "ministros/foto_form.html"

    def get_success_url(self):
        return reverse("usuarios:ministros:galeria", args=[self.object.ministro_id])

    def form_valid(self, form):
        messages.success(self.request, "Foto atualizada com sucesso.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_section": "ministros",
                "ministro": self.object.ministro,
                "page_title": "Editar foto",
                "submit_label": "Salvar foto",
            }
        )
        return context


class FotoMinistroDestaqueView(MinistroManagerRequiredMixin, View):
    def post(self, request, pk):
        foto = get_object_or_404(FotoMinistro.objects.select_related("ministro"), pk=pk)
        foto.destaque = True
        foto.save(update_fields=["destaque"])
        messages.success(request, "Foto marcada como destaque.")
        return HttpResponseRedirect(reverse("usuarios:ministros:galeria", args=[foto.ministro_id]))


class FotoMinistroDeleteView(MinistroManagerRequiredMixin, View):
    def post(self, request, pk):
        foto = get_object_or_404(FotoMinistro.objects.select_related("ministro"), pk=pk)
        ministro_id = foto.ministro_id
        foto.delete()
        messages.success(request, "Foto removida da galeria.")
        return HttpResponseRedirect(reverse("usuarios:ministros:galeria", args=[ministro_id]))


class MinistroVisitanteFormView(UpdateView):
    model = Ministro
    form_class = MinistroVisitanteForm
    template_name = "ministros/formulario_externo.html"
    slug_url_kwarg = "token"
    slug_field = "token_formulario"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.tipo != Ministro.Tipo.VISITANTE:
            return render(request, "ministros/formulario_indisponivel.html", status=404)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        ministro = form.save(commit=False)
        if ministro.status == Ministro.Status.APROVADO:
            ministro.status = Ministro.Status.ATUALIZADO
        else:
            ministro.status = Ministro.Status.PENDENTE
        ministro.tipo = Ministro.Tipo.VISITANTE
        ministro.save()
        messages.success(
            self.request,
            "Informacoes enviadas com sucesso. Nossa equipe ira revisar os dados.",
        )
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("ministros:formulario_sucesso")


class MinistroVisitanteSuccessView(TemplateView):
    template_name = "ministros/formulario_sucesso.html"
