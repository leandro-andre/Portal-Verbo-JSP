from django.urls import path

from . import views


urlpatterns = [
    path(
        "escalas/cultos-padrao/",
        views.CultoPadraoListView.as_view(),
        name="cultos_padrao_lista",
    ),
    path(
        "escalas/cultos-padrao/novo/",
        views.CultoPadraoCreateView.as_view(),
        name="culto_padrao_novo",
    ),
    path(
        "escalas/cultos-padrao/<int:pk>/editar/",
        views.CultoPadraoUpdateView.as_view(),
        name="culto_padrao_editar",
    ),
    path(
        "escalas/cultos-padrao/<int:pk>/status/",
        views.CultoPadraoStatusView.as_view(),
        name="culto_padrao_status",
    ),
    path(
        "minhas-indisponibilidades/",
        views.MinhasIndisponibilidadesListView.as_view(),
        name="minhas_indisponibilidades",
    ),
    path(
        "minhas-indisponibilidades/nova/",
        views.IndisponibilidadeCreateView.as_view(),
        name="indisponibilidade_nova",
    ),
    path(
        "minhas-indisponibilidades/<int:pk>/editar/",
        views.IndisponibilidadeUpdateView.as_view(),
        name="indisponibilidade_editar",
    ),
    path(
        "minhas-indisponibilidades/<int:pk>/cancelar/",
        views.IndisponibilidadeCancelView.as_view(),
        name="indisponibilidade_cancelar",
    ),
    path("escalas/", views.EscalaListView.as_view(), name="escala_lista"),
    path("escalas/gerar-mes/", views.GerarEscalasMesView.as_view(), name="escala_gerar_mes"),
    path("escalas/nova/", views.EscalaCreateView.as_view(), name="escala_nova"),
    path("escalas/<int:pk>/editar/", views.EscalaUpdateView.as_view(), name="escala_editar"),
    path("escalas/<int:pk>/itens/", views.EscalaItensView.as_view(), name="escala_itens"),
    path(
        "escalas/<int:pk>/itens/<int:item_id>/remover/",
        views.EscalaItemDeleteView.as_view(),
        name="escala_item_remover",
    ),
]
