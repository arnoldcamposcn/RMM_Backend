from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from .models import Articulos, ComentarioArticulo, LikeArticulo
from .serializers import ArticuloSerializer, ComentarioArticuloSerializer, LikeArticuloSerializer
from .pagination import ArticulosPagination
from drf_spectacular.utils import extend_schema

# ----------------------------
# 📌 PERMISOS PERSONALIZADOS
# ----------------------------

# ==========================
# ARTÍCULOS
# ==========================
@extend_schema(
    tags=["Artículos - listar"],
    description="Endpoints para consultar artículos con paginación y búsqueda (solo lectura)."
)
class ArticuloViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet SOLO DE LECTURA para listar y ver detalles de artículos.
    
    ⚠️ IMPORTANTE: Los artículos solo pueden ser creados/editados por administradores
    desde el Django Admin Panel.
    
    Funcionalidades:
    - 🔍 Búsqueda: ?search=término (busca en título y contenido)
    - 📄 Paginación: 6 artículos por página (?page=1, ?page_size=10)
    - 👁️ Solo lectura: GET /list/ y GET /detail/ disponibles
    
    Ejemplos de uso:
    - GET /api/v1/articles/?search=tecnología
    - GET /api/v1/articles/?page=2&page_size=10
    - GET /api/v1/articles/1/ (detalle específico)
    """
    queryset = Articulos.objects.all().order_by('-fecha_publicacion')
    serializer_class = ArticuloSerializer
    permission_classes = [permissions.AllowAny]  # Solo lectura, acceso público
    pagination_class = ArticulosPagination
    
    # Configuración de búsqueda
    filter_backends = [filters.SearchFilter]
    search_fields = ['titulo_articulo', 'contenido']

    @extend_schema(
        tags=["Artículos - Reacciones"],
        description="Dar o quitar 'me gusta' a un artículo."
    )
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def toggle_like(self, request, pk=None):
        """
        Acción para dar o quitar 'like' a un artículo completo.
        
        Comportamiento:
        - Si no ha dado like -> Se crea el like
        - Si ya dio like -> Se elimina el like
        
        No requiere payload, solo POST vacío.
        """
        articulo = get_object_or_404(Articulos, pk=pk)
        user = request.user

        # Verificar si ya existe un like del usuario
        like_obj = LikeArticulo.objects.filter(articulo=articulo, usuario=user).first()

        if like_obj:
            # Si existe, eliminarlo (quitar like)
            like_obj.delete()
            liked = False
            message = "👍 Like eliminado"
        else:
            # Si no existe, crearlo (dar like)
            LikeArticulo.objects.create(articulo=articulo, usuario=user)
            liked = True
            message = "👍 Like agregado"

        return Response(
            {
                "articulo": articulo.id,
                "usuario": user.id,
                "liked": liked,
                "likes_count": articulo.likes.count(),
                "message": message
            },
            status=status.HTTP_200_OK
        )


# ==========================
# COMENTARIOS
# ==========================
@extend_schema(
    tags=["Artículos - Comentarios"],
    description="Endpoints para consultar y crear comentarios con paginación y búsqueda."
)
class ComentarioArticuloViewSet(viewsets.ModelViewSet):
    """
    ViewSet para listar, crear, actualizar y eliminar comentarios de artículos.
    
    ⚠️ IMPORTANTE: Solo muestra comentarios principales (sin parent).
    Las respuestas aparecen anidadas en el campo 'respuestas' de cada comentario padre.
    
    Funcionalidades:
    - 🔍 Búsqueda: ?search=término (busca en el contenido del comentario)
    - 📄 Paginación: usa la configuración global de settings (5 comentarios por página)
    - 🎯 Filtro por artículo: ?articulo=1
    
    Ejemplos de uso:
    - GET /api/v1/articles/comentarios/?articulo=1 - Comentarios principales del artículo 1
    - POST /api/v1/articles/comentarios/ - Crear comentario
    
    Payload para crear comentario:
    {
        "articulo": 1,
        "contenido": "Mi comentario aquí",
        "parent": ""  // o ID del comentario padre para respuestas
    }
    """
    queryset = ComentarioArticulo.objects.filter(parent__isnull=True).order_by('-creado_en')
    serializer_class = ComentarioArticuloSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    # Configuración de filtros y búsqueda
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['articulo', 'parent']
    search_fields = ['contenido']

    def perform_create(self, serializer):
        """Crear comentario asociado al usuario autenticado"""
        serializer.save(autor=self.request.user)
