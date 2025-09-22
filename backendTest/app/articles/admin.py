from django.contrib import admin
from .models import Articulos

@admin.register(Articulos)
class ArticulosAdmin(admin.ModelAdmin):
    """
    Configuración del admin para gestionar artículos.
    Solo administradores pueden crear/editar artículos.
    Las categorías se gestionan desde Blog/Categorías y se reutilizan aquí.
    """
    list_display = ('titulo_articulo', 'categoria_articulo', 'fecha_publicacion', 'id')
    list_filter = ('fecha_publicacion', 'categoria_articulo')
    search_fields = ('titulo_articulo', 'contenido', 'categoria_articulo__nombre_categoria')
    ordering = ('-fecha_publicacion',)
    
    fieldsets = (
        ('Información del Artículo', {
            'fields': ('titulo_articulo', 'categoria_articulo', 'contenido', 'fecha_publicacion')
        }),
        ('Imágenes', {
            'fields': ('imagen_principal', 'banner'),
            'description': 'Imagen principal del artículo y banner para destacar'
        }),
    )
    
    # Configuración adicional para mejorar la experiencia de admin
    autocomplete_fields = []  # Se puede agregar si hay muchas categorías
    raw_id_fields = []  # Alternativa para muchas categorías


