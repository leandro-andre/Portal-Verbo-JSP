from django.contrib import admin

from .models import ConteudoAuditLog


@admin.register(ConteudoAuditLog)
class ConteudoAuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "criado_em",
        "usuario",
        "content_type",
        "object_id",
        "acao",
        "campo",
    )
    list_filter = ("acao", "content_type", "criado_em")
    search_fields = ("object_id", "object_repr", "campo", "valor_anterior", "valor_novo")
    readonly_fields = (
        "usuario",
        "content_type",
        "object_id",
        "object_repr",
        "acao",
        "campo",
        "valor_anterior",
        "valor_novo",
        "criado_em",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
