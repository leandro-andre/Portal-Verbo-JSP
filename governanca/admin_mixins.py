from django.contrib import admin

from .audit import log_model_create, log_model_delete, log_model_update
from .forms import GovernedModelFormMixin
from .permissions import (
    get_campos_bloqueados_por_usuario,
    usuario_pode_executar_acao_conteudo,
)


class GovernedContentAdminMixin(admin.ModelAdmin):
    field_permission_visibility_mode = "readonly"

    def get_governed_model(self):
        return self.model

    def has_module_permission(self, request):
        model = self.get_governed_model()
        return any(
            usuario_pode_executar_acao_conteudo(request.user, model, acao)
            for acao in ("view", "add", "change")
        )

    def has_view_permission(self, request, obj=None):
        model = obj or self.get_governed_model()
        return any(
            usuario_pode_executar_acao_conteudo(request.user, model, acao)
            for acao in ("view", "change")
        )

    def has_add_permission(self, request):
        return usuario_pode_executar_acao_conteudo(
            request.user,
            self.get_governed_model(),
            "add",
        )

    def has_change_permission(self, request, obj=None):
        return usuario_pode_executar_acao_conteudo(
            request.user,
            obj or self.get_governed_model(),
            "change",
        )

    def has_delete_permission(self, request, obj=None):
        return usuario_pode_executar_acao_conteudo(
            request.user,
            obj or self.get_governed_model(),
            "delete",
        )

    def get_restricted_field_names(self, request, obj=None):
        if not self.has_change_permission(request, obj):
            return []
        return get_campos_bloqueados_por_usuario(
            request.user,
            self.get_governed_model(),
            obj=obj,
        )

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if self.field_permission_visibility_mode != "readonly":
            return tuple(readonly_fields)

        for campo in self.get_restricted_field_names(request, obj):
            if campo not in readonly_fields:
                readonly_fields.append(campo)

        return tuple(readonly_fields)

    def get_exclude(self, request, obj=None):
        excluded = list(super().get_exclude(request, obj) or [])
        if self.field_permission_visibility_mode == "hide":
            for campo in self.get_restricted_field_names(request, obj):
                if campo not in excluded:
                    excluded.append(campo)
        return excluded or None

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if self.field_permission_visibility_mode != "hide":
            return fieldsets

        hidden_fields = set(self.get_restricted_field_names(request, obj))
        if not hidden_fields:
            return fieldsets

        filtered_fieldsets = []
        for title, options in fieldsets:
            fields = options.get("fields", ())
            filtered_fields = self._filter_fields_structure(fields, hidden_fields)
            if filtered_fields:
                new_options = options.copy()
                new_options["fields"] = filtered_fields
                filtered_fieldsets.append((title, new_options))

        return tuple(filtered_fieldsets)

    def _filter_fields_structure(self, fields, hidden_fields):
        filtered = []
        for item in fields:
            if isinstance(item, (list, tuple)):
                nested = self._filter_fields_structure(item, hidden_fields)
                if nested:
                    filtered.append(tuple(nested) if len(nested) > 1 else nested[0])
            elif item not in hidden_fields:
                filtered.append(item)
        return tuple(filtered)

    def get_form(self, request, obj=None, change=False, **kwargs):
        base_form = super().get_form(request, obj, change=change, **kwargs)
        governed_model = self.get_governed_model()

        class RequestAwareGovernedForm(GovernedModelFormMixin, base_form):
            def __init__(self, *args, **form_kwargs):
                form_kwargs.setdefault("request_user", request.user)
                form_kwargs.setdefault("governed_model", governed_model)
                super().__init__(*args, **form_kwargs)

        return RequestAwareGovernedForm

    def save_model(self, request, obj, form, change):
        old_obj = None
        if change:
            old_obj = self.model.objects.get(pk=obj.pk)

        super().save_model(request, obj, form, change)

        if change and old_obj is not None:
            log_model_update(request.user, old_obj, obj, form.changed_data)
        else:
            log_model_create(request.user, obj, form.changed_data)

    def delete_model(self, request, obj):
        log_model_delete(request.user, obj)
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            log_model_delete(request.user, obj)
        super().delete_queryset(request, queryset)
