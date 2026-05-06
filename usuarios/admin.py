from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    model = Usuario
    fieldsets = UserAdmin.fieldsets + (
        (
            "Informacoes adicionais",
            {
                "fields": (
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
