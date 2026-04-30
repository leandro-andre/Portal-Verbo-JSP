from django.shortcuts import render
from django.utils import timezone

from .models import Evento


def agenda(request):
    """Eventos publicados, do mais próximo ao mais distante."""
    hoje = timezone.localdate()
    eventos = (
        Evento.objects
        .filter(publicado=True, data__gte=hoje)
        .order_by("data", "horario")
    )
    return render(request, "eventos/agenda.html", {"eventos": eventos})
