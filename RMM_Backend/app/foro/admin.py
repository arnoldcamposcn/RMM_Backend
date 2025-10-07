from django.contrib import admin
# from .models import Tema, ComentarioTema, LikeTema
from .models import Categoria_Foro


# @admin.register(Tema)
# class TemaAdmin(admin.ModelAdmin):
#     """
#     Configuración del admin para gestionar temas del foro.
#     Los administradores pueden ver y moderar temas si es necesario.
#     """
#     list_display = ('titulo', 'autor', 'creado_en', 'likes_count', 'id')
#     list_filter = ('creado_en', 'autor')
#     search_fields = ('titulo', 'contenido', 'autor__email')
#     ordering = ('-creado_en',)
#     readonly_fields = ('creado_en', 'actualizado_en', 'likes_count')
    
#     fieldsets = (
#         ('Información del Tema', {
#             'fields': ('titulo', 'contenido', 'autor')
#         }),
#         ('Fechas', {
#             'fields': ('creado_en', 'actualizado_en'),
#             'classes': ('collapse',)
#         }),
#         ('Estadísticas', {
#             'fields': ('likes_count',),
#             'classes': ('collapse',)
#         }),
#     )

#     def likes_count(self, obj):
#         """Mostrar cantidad de likes"""
#         return obj.likes.count()
#     likes_count.short_description = 'Likes'


@admin.register(Categoria_Foro)
class CategoriaForoAdmin(admin.ModelAdmin):
    list_display = ('nombre_categoria', 'slug')
    search_fields = ('nombre_categoria',)
    ordering = ('nombre_categoria',)


# @admin.register(ComentarioTema)
# class ComentarioTemaAdmin(admin.ModelAdmin):
#     """
#     Configuración del admin para gestionar comentarios del foro.
#     """
#     list_display = ('contenido_corto', 'autor', 'tema', 'parent', 'creado_en', 'id')
#     list_filter = ('creado_en', 'tema', 'autor')
#     search_fields = ('contenido', 'autor__email', 'tema__titulo')
#     ordering = ('-creado_en',)
#     readonly_fields = ('creado_en',)

#     def contenido_corto(self, obj):
#         """Mostrar contenido truncado"""
#         return obj.contenido[:50] + "..." if len(obj.contenido) > 50 else obj.contenido
#     contenido_corto.short_description = 'Contenido'


# @admin.register(LikeTema)
# class LikeTemaAdmin(admin.ModelAdmin):
#     """
#     Configuración del admin para gestionar likes de temas.
#     """
#     list_display = ('usuario', 'tema', 'creado_en', 'id')
#     list_filter = ('creado_en', 'tema')
#     search_fields = ('usuario__email', 'tema__titulo')
#     ordering = ('-creado_en',)
#     readonly_fields = ('creado_en',)
