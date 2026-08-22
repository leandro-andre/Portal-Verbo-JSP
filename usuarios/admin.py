from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AccessRequest, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    model = Usuario
    fieldsets = UserAdmin.fieldsets + (
        (
            "Informacoes adicionais",
            {
                "fields": (
                    "person",
                    "telefone",
                    "foto",
                    "data_nascimento",
                    "status_eclesiastico",
                    "discipulado_concluido",
                    "discipulado_concluido_em",
                    "qualificado_por",
                    "qualificado_em",
                    "eh_pastor",
                ),
            },
        ),
    )
    readonly_fields = ("qualificado_em",)
    list_display = (
        "username",
        "person",
        "email",
        "first_name",
        "last_name",
        "status_eclesiastico",
        "eh_pastor",
        "is_staff",
    )
    list_filter = (
        "status_eclesiastico",
        "eh_pastor",
        "is_staff",
        "is_superuser",
        "is_active",
    )
    autocomplete_fields = ("person", "qualificado_por")


@admin.register(AccessRequest)
class AccessRequestAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "phone", "birth_date", "status", "usuario", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("full_name", "email", "phone")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Solicitacao",
            {
                "fields": (
                    "full_name",
                    "birth_date",
                    "email",
                    "phone",
                    "usuario",
                    "status",
                )
            },
        ),
        (
            "Revisao futura",
            {
                "fields": (
                    "person",
                    "reviewed_by",
                    "reviewed_at",
                    "rejection_reason",
                )
            },
        ),
        ("Auditoria", {"fields": ("created_at", "updated_at")}),
    )
