from django.urls import path

from . import views

app_name = "infantil"

urlpatterns = [
    path("", views.SalaListView.as_view(), name="sala_lista"),
    path("minhas-criancas/", views.MinhasCriancasListView.as_view(), name="minhas_criancas"),
    path("minhas-criancas/nova/", views.MinhaCriancaCreateView.as_view(), name="minha_crianca_nova"),
    path(
        "minhas-criancas/<int:pk>/editar/",
        views.MinhaCriancaUpdateView.as_view(),
        name="minha_crianca_editar",
    ),
    path("cadastros/", views.CadastrosInfantisListView.as_view(), name="cadastros_lista"),
    path(
        "cadastros/<int:pk>/revisar/",
        views.CadastroInfantilReviewView.as_view(),
        name="cadastro_review",
    ),
    path("salas/nova/", views.SalaCreateView.as_view(), name="sala_nova"),
    path("salas/<int:pk>/editar/", views.SalaUpdateView.as_view(), name="sala_editar"),
    path("salas/<int:pk>/equipe/", views.SalaEquipeView.as_view(), name="sala_equipe"),
    path("salas/<int:pk>/chamadas/", views.SalaChamadasView.as_view(), name="sala_chamadas"),
    path(
        "salas/<int:pk>/chamadas/<int:chamada_id>/cancelar/",
        views.ChamadaResponsavelCancelView.as_view(),
        name="chamada_cancelar",
    ),
    path(
        "salas/<int:pk>/chamadas/<int:chamada_id>/resolver/",
        views.ChamadaResponsavelResolveView.as_view(),
        name="chamada_resolver",
    ),
    path(
        "salas/<int:pk>/chamadas/<int:chamada_id>/reenviar/",
        views.ChamadaResponsavelReopenView.as_view(),
        name="chamada_reenviar",
    ),
    path(
        "salas/<int:pk>/equipe/<int:participacao_id>/status/",
        views.SalaMembroStatusView.as_view(),
        name="sala_equipe_status",
    ),
    path("salas/<int:pk>/criancas/", views.SalaCriancasView.as_view(), name="sala_criancas"),
    path("salas/<int:sala_pk>/criancas/nova/", views.CriancaCreateView.as_view(), name="crianca_nova"),
    path("criancas/<int:pk>/editar/", views.CriancaUpdateView.as_view(), name="crianca_editar"),
    path("criancas/<int:pk>/", views.CriancaDetailView.as_view(), name="crianca_detail"),
    path("salas/<int:pk>/aulas/", views.SalaAulasView.as_view(), name="sala_aulas"),
    path("salas/<int:sala_pk>/aulas/nova/", views.AulaSalaCreateView.as_view(), name="aula_nova"),
    path("aulas/<int:pk>/editar/", views.AulaSalaUpdateView.as_view(), name="aula_editar"),
    path("aulas/<int:pk>/", views.AulaSalaDetailView.as_view(), name="aula_detail"),
]
