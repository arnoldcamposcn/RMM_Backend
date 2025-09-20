from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from .models import Blog, ComentarioBlog, LikeBlog
from .serializers import BlogSerializer, ComentarioBlogSerializer, LikeBlogSerializer
from .pagination import BlogPagination
from drf_spectacular.utils import extend_schema


# ----------------------------
# 📌 PERMISOS PERSONALIZADOS
# ----------------------------

# ==========================
# BLOGS
# ==========================
@extend_schema(
    tags=["Blogs - listar"],
    description="Endpoints para consultar blogs con paginación y búsqueda (solo lectura)."
)
class BlogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet SOLO DE LECTURA para listar y ver detalles de blogs.
    
    ⚠️ IMPORTANTE: Los blogs solo pueden ser creados/editados por administradores
    desde el Django Admin Panel.
    
    Funcionalidades:
    - 🔍 Búsqueda: ?search=término (busca en título y contenido)
    - 📄 Paginación: 5 blogs por página (?page=1, ?page_size=10)
    - 👁️ Solo lectura: GET /list/ y GET /detail/ disponibles
    
    Ejemplos de uso:
    - GET /api/v1/blog/?search=django
    - GET /api/v1/blog/?page=2&page_size=10
    - GET /api/v1/blog/1/ (detalle específico)
    """
    queryset = Blog.objects.all().order_by('-fecha_publicacion')
    serializer_class = BlogSerializer
    permission_classes = [permissions.AllowAny]  # Solo lectura, acceso público
    pagination_class = BlogPagination
    
    # Configuración de búsqueda
    filter_backends = [filters.SearchFilter]
    search_fields = ['titulo_blog', 'contenido']

    @extend_schema(
        tags=["Blogs - Reacciones"],
        description="Dar o quitar 'me gusta' a un blog."
    )
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def toggle_like(self, request, pk=None):
        """
        Acción para dar o quitar 'like' a un blog completo.
        
        Comportamiento:
        - Si no ha dado like -> Se crea el like
        - Si ya dio like -> Se elimina el like
        
        No requiere payload, solo POST vacío.
        """
        blog = get_object_or_404(Blog, pk=pk)
        user = request.user

        # Verificar si ya existe un like del usuario
        like_obj = LikeBlog.objects.filter(blog=blog, usuario=user).first()

        if like_obj:
            # Si existe, eliminarlo (quitar like)
            like_obj.delete()
            liked = False
            message = "👍 Like eliminado"
        else:
            # Si no existe, crearlo (dar like)
            LikeBlog.objects.create(blog=blog, usuario=user)
            liked = True
            message = "👍 Like agregado"

        return Response(
            {
                "blog": blog.id,
                "usuario": user.id,
                "liked": liked,
                "likes_count": blog.likes.count(),
                "message": message
            },
            status=status.HTTP_200_OK
        )


# ==========================
# COMENTARIOS
# ==========================
@extend_schema(
    tags=["Blogs - Comentarios"],
    description="Endpoints para consultar y crear comentarios con paginación y búsqueda."
)
class ComentarioBlogViewSet(viewsets.ModelViewSet):
    """
    ViewSet para listar, crear, actualizar y eliminar comentarios de blogs.
    
    ⚠️ IMPORTANTE: Solo muestra comentarios principales (sin parent).
    Las respuestas aparecen anidadas en el campo 'respuestas' de cada comentario padre.
    
    Funcionalidades:
    - 🔍 Búsqueda: ?search=término (busca en el contenido del comentario)
    - 📄 Paginación: usa la configuración global de settings (5 comentarios por página)
    - 🎯 Filtro por blog: ?blog=1
    
    Ejemplos de uso:
    - GET /api/v1/blog/comentarios/?blog=1 - Comentarios principales del blog 1
    - POST /api/v1/blog/comentarios/ - Crear comentario
    
    Payload para crear comentario:
    {
        "blog": 1,
        "contenido": "Mi comentario aquí",
        "parent": ""  // o ID del comentario padre para respuestas
    }
    """
    queryset = ComentarioBlog.objects.filter(parent__isnull=True).order_by('-creado_en')
    serializer_class = ComentarioBlogSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    # Configuración de filtros y búsqueda
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['blog', 'parent']
    search_fields = ['contenido']

    def perform_create(self, serializer):
        """Crear comentario asociado al usuario autenticado"""
        serializer.save(autor=self.request.user)
