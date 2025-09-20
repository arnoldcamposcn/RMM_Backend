from django.contrib import admin
from django.utils.html import format_html
from .models import Ediciones

@admin.register(Ediciones)
class EdicionesAdmin(admin.ModelAdmin):
    list_display = ("numero_edicion", "titulo_edicion", "fecha_publicacion", "preview_image")
    list_filter = ("fecha_publicacion",)
    search_fields = ("titulo_edicion", "numero_edicion")
    ordering = ("-numero_edicion", "-fecha_publicacion")
    date_hierarchy = "fecha_publicacion"

    def preview_image(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" style="width: 60px; height: auto;" />', obj.imagen.url)
        return "Sin imagen"
    preview_image.short_description = "Vista previa"

