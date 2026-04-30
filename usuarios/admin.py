from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """
    Customização do Admin de Usuários para incluir os novos campos.
    """
    model = Usuario
    
    # Adicionando os novos campos aos fieldsets do UserAdmin original
    fieldsets = UserAdmin.fieldsets + (
        ("Informações Adicionais", {
            "fields": ("telefone", "foto", "data_nascimento", "is_membro"),
        }),
    )
    
    # Campos que aparecerão na listagem
    list_display = ("username", "email", "first_name", "last_name", "is_membro", "is_staff")
    list_filter = ("is_membro", "is_staff", "is_superuser", "is_active")
