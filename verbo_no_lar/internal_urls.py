from django.urls import path

from . import views


app_name = "verbo_no_lar"


urlpatterns = [
    # Casas
    path("casas/", views.CasaListView.as_view(), name="casa_lista"),
    path("casas/nova/", views.CasaCreateView.as_view(), name="casa_nova"),
    path("casas/<int:pk>/", views.CasaDetailView.as_view(), name="casa_detalhe"),
    path("casas/<int:pk>/editar/", views.CasaUpdateView.as_view(), name="casa_editar"),
    # Participantes
    path("casas/<int:casa_pk>/participantes/", views.ParticipanteListView.as_view(), name="participantes"),
    path("casas/<int:casa_pk>/participantes/novo/", views.ParticipanteCreateView.as_view(), name="participante_novo"),
    path("participantes/<int:pk>/editar/", views.ParticipanteUpdateView.as_view(), name="participante_editar"),
    # Escalas
    path("casas/<int:casa_pk>/escalas/", views.EscalaListView.as_view(), name="escalas"),
    path("casas/<int:casa_pk>/escalas/nova/", views.EscalaCreateView.as_view(), name="escala_nova"),
    path("escalas/<int:pk>/editar/", views.EscalaUpdateView.as_view(), name="escala_editar"),
    # Materiais
    path("materiais/", views.MaterialListView.as_view(), name="materiais"),
    path("materiais/novo/", views.MaterialCreateView.as_view(), name="material_novo"),
    path("materiais/<int:pk>/", views.MaterialDetailView.as_view(), name="material_detalhe"),
    path("materiais/<int:pk>/editar/", views.MaterialUpdateView.as_view(), name="material_editar"),
    # Relatórios
    path("casas/<int:casa_pk>/relatorios/", views.RelatorioListView.as_view(), name="relatorios"),
    path("casas/<int:casa_pk>/relatorios/novo/", views.RelatorioCreateView.as_view(), name="relatorio_novo"),
    path("relatorios/<int:pk>/", views.RelatorioDetailView.as_view(), name="relatorio_detalhe"),
]

