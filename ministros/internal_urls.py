from django.urls import path

from . import views


app_name = "ministros"

urlpatterns = [
    path("", views.MinistroListView.as_view(), name="lista"),
    path("novo/", views.MinistroCreateView.as_view(), name="novo"),
    path("galeria/", views.FotoMinistroListView.as_view(), name="galeria_lista"),
    path("<int:pk>/", views.MinistroDetailView.as_view(), name="detalhe"),
    path("<int:pk>/editar/", views.MinistroUpdateView.as_view(), name="editar"),
    path("<int:pk>/token/", views.MinistroTokenRegenerateView.as_view(), name="regenerar_token"),
    path("<int:pk>/galeria/", views.MinistroGaleriaView.as_view(), name="galeria"),
    path("fotos/<int:pk>/editar/", views.FotoMinistroUpdateView.as_view(), name="foto_editar"),
    path("fotos/<int:pk>/destaque/", views.FotoMinistroDestaqueView.as_view(), name="foto_destaque"),
    path("fotos/<int:pk>/excluir/", views.FotoMinistroDeleteView.as_view(), name="foto_excluir"),
]
