from core.models import SiteConfig, SobrePage
from eventos.models import Evento
from governanca.audit import log_model_create, log_model_update
from noticias.models import Noticia


def atualizar_site_config(form, usuario):
    old_obj = SiteConfig.objects.get(pk=form.instance.pk)
    objeto = form.save()
    log_model_update(usuario, old_obj, objeto, form.changed_data)
    return objeto


def atualizar_transmissao_ao_vivo(form, usuario):
    return atualizar_site_config(form, usuario)


def atualizar_sobre_page(form, lider_formset, usuario):
    old_obj = SobrePage.objects.get(pk=form.instance.pk)
    objeto = form.save()
    lider_formset.instance = objeto
    lider_formset.save()
    log_model_update(usuario, old_obj, objeto, form.changed_data)
    return objeto


def criar_evento_publico(form, usuario):
    evento = form.save()
    log_model_create(usuario, evento, form.changed_data)
    return evento


def atualizar_evento_publico(form, usuario):
    old_obj = Evento.objects.get(pk=form.instance.pk)
    evento = form.save()
    log_model_update(usuario, old_obj, evento, form.changed_data)
    return evento


def alternar_publicacao_evento(evento, usuario):
    old_obj = Evento.objects.get(pk=evento.pk)
    evento.publicado = not evento.publicado
    evento.save(update_fields=["publicado"])
    log_model_update(usuario, old_obj, evento, ["publicado"])
    return evento


def criar_noticia_publica(form, usuario):
    noticia = form.save()
    log_model_create(usuario, noticia, form.changed_data)
    return noticia


def atualizar_noticia_publica(form, usuario):
    old_obj = Noticia.objects.get(pk=form.instance.pk)
    noticia = form.save()
    log_model_update(usuario, old_obj, noticia, form.changed_data)
    return noticia


def alternar_publicacao_noticia(noticia, usuario):
    old_obj = Noticia.objects.get(pk=noticia.pk)
    noticia.publicado = not noticia.publicado
    noticia.save(update_fields=["publicado"])
    log_model_update(usuario, old_obj, noticia, ["publicado"])
    return noticia
