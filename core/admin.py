from django.contrib import admin


class AuditableAdmin(admin.ModelAdmin):
    readonly_fields = (
        'creado_por',
        'modificado_por',
        'fecha_creacion',
        'fecha_actualizacion',
    )

    auditable_list_display = (
        'activo',
        'eliminado',
        'creado_por',
        'modificado_por',
        'fecha_creacion',
    )

    auditable_list_filter = (
        'activo',
        'eliminado',
        'fecha_creacion',
        'fecha_actualizacion',
    )

    auditable_readonly_fields = (
        'creado_por',
        'modificado_por',
        'fecha_creacion',
        'fecha_actualizacion',
    )

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))

        for field in self.auditable_readonly_fields:
            if field not in readonly_fields:
                readonly_fields.append(field)

        return readonly_fields

    def get_list_display(self, request):
        list_display = list(super().get_list_display(request))

        for field in self.auditable_list_display:
            if field not in list_display:
                list_display.append(field)

        return list_display

    def get_list_filter(self, request):
        list_filter = list(super().get_list_filter(request))

        for field in self.auditable_list_filter:
            if field not in list_filter:
                list_filter.append(field)

        return list_filter

    def save_model(self, request, obj, form, change):
        if not change and hasattr(obj, 'creado_por'):
            obj.creado_por = request.user

        if hasattr(obj, 'modificado_por'):
            obj.modificado_por = request.user

        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        obj.delete()

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete()