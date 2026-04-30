from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import Noticia


def lista(request):
    """Lista todas as notícias publicadas até hoje, ordenadas de forma decrescente."""
    hoje = timezone.localdate()
    noticias = (
        Noticia.objects
        .filter(publicado=True, data_publicacao__lte=hoje)
        .order_by("-data_publicacao", "-criado_em")
    )
    return render(request, "noticias/lista.html", {"noticias": noticias})


def detalhe(request, slug: str):
    """Exibe o detalhe de uma notícia publicada usando seu slug."""
    hoje = timezone.localdate()
    noticia = get_object_or_404(Noticia, slug=slug, publicado=True, data_publicacao__lte=hoje)
    outras_noticias = (
        Noticia.objects
        .filter(publicado=True, data_publicacao__lte=hoje)
        .exclude(id=noticia.id)
        .order_by("-data_publicacao", "-criado_em")[:3]
    )
    return render(
        request,
        "noticias/detalhe.html",
        {"noticia": noticia, "outras_noticias": outras_noticias},
    )
