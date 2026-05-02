from django.urls import path

from . import views

app_name = "eventos"

urlpatterns = [
    # Gestão (área interna)
    path("gestao/", views.EventoInternoListView.as_view(), name="interno_lista"),
    path("gestao/novo/", views.EventoCreateView.as_view(), name="novo"),
    path("gestao/<int:pk>/", views.EventoDetailView.as_view(), name="interno_detalhe"),
    path("gestao/<int:pk>/editar/", views.EventoUpdateView.as_view(), name="editar"),
    path("gestao/<int:pk>/inscricoes/", views.EventoInscricaoListView.as_view(), name="inscricoes"),
    path("gestao/<int:pk>/check-in/", views.EventoCheckinView.as_view(), name="checkin"),
    path("gestao/<int:pk>/leitor-qr/", views.EventoLeitorQRCodeView.as_view(), name="leitor_qr"),
    path("gestao/<int:pk>/api/check-in/", views.EventoCheckinApiView.as_view(), name="checkin_api"),
    path(
        "gestao/<int:pk>/check-in/<int:inscricao_pk>/",
        views.EventoMarcarPresencaView.as_view(),
        name="marcar_presenca",
    ),
    # Jornada do usuário (logado)
    path("<int:pk>/inscricao/", views.EventoInscricaoCreateView.as_view(), name="inscrever"),
    path("minhas-inscricoes/", views.MinhasInscricoesView.as_view(), name="minhas_inscricoes"),
    path("minhas-inscricoes/<int:pk>/", views.MinhaInscricaoDetailView.as_view(), name="minha_inscricao"),
    path("minhas-inscricoes/<int:pk>/qrcode.png", views.InscricaoQRCodeView.as_view(), name="inscricao_qrcode"),
    path(
        "minhas-inscricoes/<int:pk>/cancelar/",
        views.CancelarMinhaInscricaoView.as_view(),
        name="cancelar_inscricao",
    ),
]

