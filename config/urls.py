"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from django.conf.urls.static import static
from core.views import react_app

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", include("usuarios.api_urls")),
    path("api/", include("church_journey.urls")),
    path("api/", include("departamentos.api_urls")),
    path("api/people/", include("pessoas.urls")),
    path("api/worship/", include("worship.urls")),
    path("api/scheduling/", include("scheduling.urls")),
    path("usuarios/", include("usuarios.urls")),
    path("", include("core.urls")),
    path("", include("eventos.urls")),
    path("", include("noticias.urls")),
    path("", include("ministros.urls")),
    path("financeiro/", include("financeiro.urls")),
]

if settings.SERVE_REACT_APP:
    urlpatterns.insert(1, path("", react_app, name="react-app"))
    urlpatterns.append(
        re_path(
            r"^(?!(?:api|admin|static|media)(?:/|$)).*$",
            react_app,
            name="react-app-fallback",
        )
    )

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
