from django import template
from django.utils import timezone

from core.models import ContatoMensagem
from departamentos.models import Departamento, DepartmentMembership
from eventos.models import Evento
from noticias.models import Noticia
from scheduling.selectors import (
    get_operational_schedule_dashboard_counts,
    get_upcoming_published_schedules,
)

register = template.Library()


@register.simple_tag
def get_dashboard_stats():
    hoje = timezone.localdate()

    total_eventos = Evento.objects.count()
    eventos_publicados = Evento.objects.filter(publicado=True).count()

    total_noticias = Noticia.objects.count()
    noticias_publicadas = Noticia.objects.filter(publicado=True).count()

    total_mensagens = ContatoMensagem.objects.count()
    mensagens_pendentes = ContatoMensagem.objects.filter(respondida=False).count()
    total_departamentos = Departamento.objects.count()
    membros_em_departamentos = DepartmentMembership.objects.filter(
        status=DepartmentMembership.Status.ACTIVE
    ).count()
    schedule_counts = get_operational_schedule_dashboard_counts(today=hoje)
    escalas_ativas = schedule_counts["published_upcoming"]

    proximos_eventos = Evento.objects.filter(data_inicio__gte=hoje).order_by("data_inicio", "horario")[:5]
    proximas_escalas = get_upcoming_published_schedules(today=hoje)[:5]
    ultimas_noticias = Noticia.objects.order_by("-data_publicacao", "-criado_em")[:5]
    ultimas_mensagens = ContatoMensagem.objects.order_by("-criado_em")[:5]

    return {
        "total_eventos": total_eventos,
        "eventos_publicados": eventos_publicados,
        "total_noticias": total_noticias,
        "noticias_publicadas": noticias_publicadas,
        "total_mensagens": total_mensagens,
        "mensagens_pendentes": mensagens_pendentes,
        "total_departamentos": total_departamentos,
        "membros_em_departamentos": membros_em_departamentos,
        "escalas_ativas": escalas_ativas,
        "escalas_rascunho": schedule_counts["draft_upcoming"],
        "pessoas_escaladas": schedule_counts["assignments_upcoming"],
        "proximos_eventos": proximos_eventos,
        "proximas_escalas": proximas_escalas,
        "ultimas_noticias": ultimas_noticias,
        "ultimas_mensagens": ultimas_mensagens,
    }
