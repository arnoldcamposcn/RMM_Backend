from django.contrib import admin
from .models import Articulos

@admin.register(Articulos)
class ArticulosAdmin(admin.ModelAdmin):
    """
    Configuración del admin para gestionar artículos.
    Solo administradores pueden crear/editar artículos.
    """
    list_display = ('titulo_articulo', 'fecha_publicacion', 'id')
    list_filter = ('fecha_publicacion',)
    search_fields = ('titulo_articulo', 'contenido')
    ordering = ('-fecha_publicacion',)
    
    fieldsets = (
        ('Información del Artículo', {
            'fields': ('titulo_articulo', 'contenido', 'fecha_publicacion')
        }),
        ('Imágenes', {
            'fields': ('imagen_principal', 'banner'),
            'description': 'Imagen principal del artículo y banner para destacar'
        }),
    )


