from django import template
from django.utils import timezone

from core.models import ContatoMensagem
from departamentos.models import Departamento, DepartamentoMembro
from escalas.models import Escala
from eventos.models import Evento
from noticias.models import Noticia

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
    membros_em_departamentos = DepartamentoMembro.objects.filter(ativo=True).count()
    escalas_ativas = Escala.objects.filter(ativa=True).count()

    proximos_eventos = Evento.objects.filter(data_inicio__gte=hoje).order_by("data_inicio", "horario")[:5]
    proximas_escalas = Escala.objects.filter(ativa=True, data__gte=hoje).select_related("departamento").order_by("data", "horario")[:5]
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
        "proximos_eventos": proximos_eventos,
        "proximas_escalas": proximas_escalas,
        "ultimas_noticias": ultimas_noticias,
        "ultimas_mensagens": ultimas_mensagens,
    }
