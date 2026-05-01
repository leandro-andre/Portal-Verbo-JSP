from django.urls import include, path

from . import views


app_name = "usuarios"

urlpatterns = [
    path("login/", views.UsuarioLoginView.as_view(), name="login"),
    path("logout/", views.UsuarioLogoutView.as_view(), name="logout"),
    path("registro/", views.RegistroView.as_view(), name="registro"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("perfil/", views.PerfilView.as_view(), name="perfil"),
    path("departamentos/", include("departamentos.urls", namespace="departamentos")),
    path("eventos/", include("eventos.internal_urls", namespace="eventos")),
    path("infantil/", include("infantil.urls", namespace="infantil")),
    path("conteudo/", include("conteudo_interno.urls", namespace="conteudo")),
    path("ministros/", include("ministros.internal_urls", namespace="ministros")),
]
