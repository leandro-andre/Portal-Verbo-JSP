import logging

from django.contrib import messages
from django.conf import settings
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import ContatoForm
from .models import SiteConfig, SobrePage
from eventos.models import Evento
from noticias.models import Noticia


logger = logging.getLogger(__name__)


def home(request):
    hoje = timezone.localdate()
    destaques = (
        Evento.objects
        .filter(publicado=True, destaque_home=True, data_inicio__gte=hoje)
        .order_by("data_inicio", "horario")[:6]
    )
    ultimas_noticias = (
        Noticia.objects
        .filter(publicado=True, destaque_home=True, data_publicacao__lte=hoje)
        .order_by("-data_publicacao", "-criado_em")[:3]
    )
    return render(request, "core/home.html", {
        "destaques": destaques,
        "ultimas_noticias": ultimas_noticias,
    })


def sobre(request):
    sobre_page = SobrePage.load()
    return render(request, "core/sobre.html", {
        "sobre": sobre_page,
    })


def contato(request):
    if request.method == "POST":
        form = ContatoForm(request.POST)
        if form.is_valid():
            contato = form.save(commit=False)
            if request.user.is_authenticated:
                contato.usuario = request.user
            contato.save()
            messages.success(
                request,
                "Mensagem enviada com sucesso. Nossa equipe vai retornar em breve.",
            )
            return redirect("core:contato")
        messages.error(
            request,
            "Nao foi possivel enviar sua mensagem. Revise os campos destacados.",
        )
    else:
        initial = {}
        if request.user.is_authenticated:
            nome = request.user.get_full_name().strip()
            if nome:
                initial["nome"] = nome
            if request.user.email:
                initial["email"] = request.user.email
        form = ContatoForm(initial=initial)

    return render(request, "core/contato.html", {"form": form})


def ao_vivo(request):
    site, _ = SiteConfig.objects.get_or_create(id=1)
    youtube_src = site.youtube_embed_url_normalized
    youtube_watch_url = site.youtube_watch_url
    return render(
        request,
        "core/ao_vivo.html",
        {
            "youtube_src": youtube_src,
            "youtube_watch_url": youtube_watch_url,
        },
    )


def react_app(request, path=""):
    index_path = settings.REACT_BUILD_DIR / "index.html"
    if not index_path.exists():
        logger.error("React build index.html nao encontrado em %s", index_path)
        raise Http404("React build nao encontrado. Execute npm run build.")
    try:
        return FileResponse(index_path.open("rb"), content_type="text/html")
    except OSError:
        logger.exception("Falha ao servir React index.html em %s", index_path)
        raise Http404("React build nao pode ser carregado.")
