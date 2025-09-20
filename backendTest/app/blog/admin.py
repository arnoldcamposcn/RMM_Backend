from django.contrib import admin
from .models import Blog, LikeBlog, Categoria_Blog

@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    """
    Configuración del admin para gestionar blogs.
    Solo administradores pueden crear/editar blogs.
    """
    list_display = ('titulo_blog', 'categoria_blog', 'fecha_publicacion', 'id')
    list_filter = ('fecha_publicacion', 'categoria_blog')
    search_fields = ('titulo_blog', 'contenido', 'categoria_blog__nombre_categoria')
    ordering = ('-fecha_publicacion',)
    
    fieldsets = (
        ('Información del Blog', {
            'fields': ('titulo_blog', 'categoria_blog', 'contenido', 'fecha_publicacion')
        }),
        ('Imágenes', {
            'fields': ('imagen_principal', 'banner'),
            'description': 'Imagen principal del blog y banner para destacar'
        }),
        ('Artículos Relacionados', {
            'fields': ('articulos',),
            'classes': ('collapse',),
            'description': 'Selecciona los artículos relacionados con este blog'
        }),
    )
    
    # Configuración para el campo ManyToMany de artículos
    filter_horizontal = ('articulos',)  # Hace más fácil la selección de múltiples artículos

@admin.register(Categoria_Blog)
class CategoriaBlogAdmin(admin.ModelAdmin):
    list_display = ('nombre_categoria', 'slug')
    search_fields = ('nombre_categoria',)
    ordering = ('nombre_categoria',)
    readonly_fields = ('slug',) 

