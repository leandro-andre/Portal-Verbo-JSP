from django.urls import path

from . import views


app_name = "conteudo_interno"

urlpatterns = [
    path("secretaria/", views.SecretariaDashboardView.as_view(), name="secretaria_dashboard"),
    path("secretaria/site/", views.SecretariaSiteConfigUpdateView.as_view(), name="secretaria_site"),
    path("secretaria/contato/", views.SecretariaContatoUpdateView.as_view(), name="secretaria_contato"),
    path("secretaria/sobre/", views.SecretariaSobreUpdateView.as_view(), name="secretaria_sobre"),
    path("secretaria/eventos/", views.SecretariaEventoListView.as_view(), name="secretaria_eventos"),
    path("secretaria/eventos/novo/", views.SecretariaEventoCreateView.as_view(), name="secretaria_evento_novo"),
    path(
        "secretaria/eventos/<int:pk>/editar/",
        views.SecretariaEventoUpdateView.as_view(),
        name="secretaria_evento_editar",
    ),
    path(
        "secretaria/eventos/<int:pk>/status/",
        views.SecretariaEventoPublishToggleView.as_view(),
        name="secretaria_evento_status",
    ),
    path("secretaria/noticias/", views.SecretariaNoticiaListView.as_view(), name="secretaria_noticias"),
    path("secretaria/noticias/nova/", views.SecretariaNoticiaCreateView.as_view(), name="secretaria_noticia_nova"),
    path(
        "secretaria/noticias/<int:pk>/editar/",
        views.SecretariaNoticiaUpdateView.as_view(),
        name="secretaria_noticia_editar",
    ),
    path(
        "secretaria/noticias/<int:pk>/status/",
        views.SecretariaNoticiaPublishToggleView.as_view(),
        name="secretaria_noticia_status",
    ),
    path("midia/ao-vivo/", views.MidiaAoVivoUpdateView.as_view(), name="midia_ao_vivo"),
    path(
        "midia/chamadas/<int:pk>/exibido/",
        views.MidiaChamadaExibidoView.as_view(),
        name="midia_chamada_exibido",
    ),
    path(
        "midia/chamadas/<int:pk>/resolvido/",
        views.MidiaChamadaResolvidoView.as_view(),
        name="midia_chamada_resolvido",
    ),
    path(
        "midia/chamadas/pendentes/",
        views.MidiaChamadasPendentesJsonView.as_view(),
        name="midia_chamadas_pendentes",
    ),
]
