from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView, UpdateView
from django.views.generic.edit import FormView

from core.models import ContatoMensagem
from departamentos.models import DepartamentoMembro
from escalas.models import EscalaItem
from eventos.models import Evento
from noticias.models import Noticia

from .forms import LoginForm, PerfilForm, RegistroForm


def get_profile_status(user):
    fields = {
        "nome": user.first_name,
        "sobrenome": user.last_name,
        "e-mail": user.email,
        "telefone": getattr(user, "telefone", ""),
        "data de nascimento": getattr(user, "data_nascimento", None),
    }
    missing_fields = [label for label, value in fields.items() if not value]
    completed = len(fields) - len(missing_fields)
    completion = round((completed / len(fields)) * 100)
    return {
        "completion": completion,
        "missing_fields": missing_fields,
    }


class UsuarioLoginView(LoginView):
    template_name = "usuarios/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


class UsuarioLogoutView(LogoutView):
    next_page = reverse_lazy("core:home")


class RegistroView(FormView):
    template_name = "usuarios/registro.html"
    form_class = RegistroForm
    success_url = reverse_lazy("usuarios:dashboard")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("usuarios:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, "Cadastro realizado com sucesso.")
        return super().form_valid(form)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "usuarios/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.localdate()

        context.update(
            {
                "profile_status": get_profile_status(user),
                "minhas_participacoes": DepartamentoMembro.objects.select_related(
                    "departamento"
                )
                .filter(membro=user, ativo=True)
                .order_by("departamento__nome"),
                "minhas_escalas": EscalaItem.objects.select_related(
                    "escala",
                    "escala__departamento",
                    "participacao",
                )
                .filter(
                    participacao__membro=user,
                    participacao__ativo=True,
                    escala__ativa=True,
                    escala__data__gte=today,
                )
                .order_by("escala__data", "escala__horario")[:5],
                "proximos_eventos": Evento.objects.filter(
                    publicado=True,
                    data_inicio__gte=today,
                ).order_by("data_inicio", "horario")[:5],
                "ultimas_noticias": Noticia.objects.filter(publicado=True).order_by(
                    "-data_publicacao",
                    "-criado_em",
                )[:5],
                "minhas_mensagens": ContatoMensagem.objects.filter(usuario=user).order_by(
                    "-criado_em"
                )[:5],
            }
        )
        return context


class PerfilView(LoginRequiredMixin, UpdateView):
    form_class = PerfilForm
    template_name = "usuarios/perfil.html"
    success_url = reverse_lazy("usuarios:perfil")

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile_status"] = get_profile_status(self.request.user)
        return context

    def form_valid(self, form):
        messages.success(self.request, "Perfil atualizado com sucesso.")
        return super().form_valid(form)
