from django.urls import path

from . import views


urlpatterns = [
    path("templates/", views.TemplateListCreateView.as_view(), name="worship-template-list"),
    path("templates/<int:pk>/", views.TemplateDetailView.as_view(), name="worship-template-detail"),
    path("templates/<int:pk>/deactivate/", views.TemplateDeactivateView.as_view(), name="worship-template-deactivate"),
    path("templates/<int:pk>/reactivate/", views.TemplateReactivateView.as_view(), name="worship-template-reactivate"),
    path("services/", views.ServiceListView.as_view(), name="worship-service-list"),
    path("services/generate/", views.GenerateServicesView.as_view(), name="worship-service-generate"),
    path("services/extraordinary/", views.ExtraordinaryServiceCreateView.as_view(), name="worship-service-extraordinary"),
    path("services/<int:pk>/", views.ServiceDetailView.as_view(), name="worship-service-detail"),
    path("services/<int:pk>/cancel/", views.ServiceCancelView.as_view(), name="worship-service-cancel"),
    path("services/<int:pk>/reactivate/", views.ServiceReactivateView.as_view(), name="worship-service-reactivate"),
]
