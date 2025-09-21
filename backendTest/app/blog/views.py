from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from .models import Blog, ComentarioBlog, LikeBlog
from .serializers import BlogSerializer, ComentarioBlogSerializer, LikeBlogSerializer
from .pagination import BlogPagination
from drf_spectacular.utils import extend_schema
from app.articles.serializers import ArticuloSerializer

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
    - 📌 Cada blog incluye su categoría, artículos relacionados, comentarios y likes

    Ejemplos de uso:
    - GET /api/v1/blog/?search=django
    - GET /api/v1/blog/?page=2&page_size=10
    - GET /api/v1/blog/1/ (detalle específico con artículos y comentarios)
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

        Comportamiento estricto:
        - Requiere especificar la acción: "add" o "remove"
        - Si action="add" y ya tiene like -> ERROR 400
        - Si action="remove" y no tiene like -> ERROR 400
        - Solo permite toggle automático si no se especifica action

        Payload requerido para validación estricta:
        {
            "action": "add"    // Para dar like
            "action": "remove" // Para quitar like
        }
        
        Si no se envía "action", funciona como toggle (comportamiento anterior).
        """
        blog = get_object_or_404(Blog, pk=pk)
        user = request.user
        
        # Obtener la acción solicitada
        action = request.data.get('action', None)
        
        # Verificar el estado actual del like
        like_obj = LikeBlog.objects.filter(blog=blog, usuario=user).first()
        has_like = bool(like_obj)

        # Si se especifica una acción, validar estrictamente
        if action == "add":
            if has_like:
                # Ya tiene like, no puede dar like otra vez
                return Response(
                    {
                        "error": "Like duplicado",
                        "message": "Ya has dado like a este blog anteriormente.",
                        "code": "DUPLICATE_LIKE",
                        "blog": blog.id,
                        "usuario": user.id,
                        "liked": True,
                        "likes_count": blog.likes.count()
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                # No tiene like, crear uno nuevo
                LikeBlog.objects.create(blog=blog, usuario=user)
                return Response(
                    {
                        "blog": blog.id,
                        "usuario": user.id,
                        "liked": True,
                        "likes_count": blog.likes.count(),
                        "message": "👍 Like agregado exitosamente"
                    },
                    status=status.HTTP_200_OK
                )
                
        elif action == "remove":
            if not has_like:
                # No tiene like, no puede quitar lo que no existe
                return Response(
                    {
                        "error": "Like no encontrado",
                        "message": "No has dado like a este blog anteriormente.",
                        "code": "LIKE_NOT_FOUND",
                        "blog": blog.id,
                        "usuario": user.id,
                        "liked": False,
                        "likes_count": blog.likes.count()
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                # Tiene like, eliminarlo
                like_obj.delete()
                return Response(
                    {
                        "blog": blog.id,
                        "usuario": user.id,
                        "liked": False,
                        "likes_count": blog.likes.count(),
                        "message": "👍 Like eliminado exitosamente"
                    },
                    status=status.HTTP_200_OK
                )
        
        # Si no se especifica action, comportamiento toggle (para compatibilidad)
        else:
            if like_obj:
                like_obj.delete()
                liked = False
                message = "👍 Like eliminado"
            else:
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

    @extend_schema(
        tags=["Blogs - Reacciones"],
        description="Obtener lista de usuarios que dieron like a un blog específico."
    )
    @action(detail=True, methods=["get"], permission_classes=[permissions.AllowAny])
    def likes_list(self, request, pk=None):
        """
        Endpoint para obtener la lista de usuarios que dieron like a un blog específico.
        
        Permite al frontend:
        - Validar si el usuario autenticado está en la lista
        - Mostrar el corazón en rojo si ya dio like
        - Obtener información de todos los usuarios que dieron like
        
        Respuesta incluye:
        - Lista de usuarios con información básica (id, email, usuario_unico)
        - Total de likes
        - Estado del usuario autenticado (si está logueado)
        """
        blog = get_object_or_404(Blog, pk=pk)
        
        # Obtener todos los likes del blog
        likes = LikeBlog.objects.filter(blog=blog).select_related('usuario').order_by('-creado_en')
        
        # Serializar la información de los usuarios
        from .serializers import LikeBlogSerializer
        likes_data = LikeBlogSerializer(likes, many=True).data
        
        # Información del usuario autenticado si está logueado
        user_liked = False
        user_info = None
        
        if request.user.is_authenticated:
            user_like = LikeBlog.objects.filter(blog=blog, usuario=request.user).first()
            user_liked = bool(user_like)
            user_info = {
                "id": request.user.id,
                "email": request.user.email,
                "usuario_unico": request.user.usuario_unico,
                "liked": user_liked
            }
        
        return Response(
            {
                "blog": {
                    "id": blog.id,
                    "titulo": blog.titulo_blog,
                    "likes_count": likes.count()
                },
                "likes_list": likes_data,
                "current_user": user_info,
                "user_liked": user_liked,
                "total_likes": likes.count()
            },
            status=status.HTTP_200_OK
        )

    @extend_schema(
        tags=["Blogs - Artículos"],
        description="Lista todos los artículos relacionados con un blog específico."
    )
    @action(detail=True, methods=["get"], permission_classes=[permissions.AllowAny])
    def articulos(self, request, pk=None):
        """
        Endpoint dedicado para traer SOLO los artículos de un blog.
        (También están disponibles directamente en el GET del blog).
        """
        blog = get_object_or_404(Blog, pk=pk)
        articulos = blog.articulos.all()
        serializer = ArticuloSerializer(articulos, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Blogs - Comentarios"],
        description="Lista todos los comentarios principales de un blog específico con paginación."
    )
    @action(detail=True, methods=["get"], permission_classes=[permissions.AllowAny])
    def comentarios(self, request, pk=None):
        """
        Endpoint dedicado para traer SOLO los comentarios principales de un blog.
        Incluye paginación y respuestas anidadas.
        
        Parámetros de consulta:
        - page: Número de página (ej: ?page=2)
        - page_size: Cantidad por página (ej: ?page_size=10)
        - search: Buscar en contenido (ej: ?search=excelente)
        """
        blog = get_object_or_404(Blog, pk=pk)
        
        # Obtener comentarios principales del blog
        comentarios = ComentarioBlog.objects.filter(
            blog=blog, 
            parent__isnull=True
        ).select_related('autor').order_by('-creado_en')
        
        # Aplicar búsqueda si se proporciona
        search = request.query_params.get('search')
        if search:
            comentarios = comentarios.filter(contenido__icontains=search)
        
        # Aplicar paginación
        paginator = BlogPagination()
        page = paginator.paginate_queryset(comentarios, request, view=self)
        
        if page is not None:
            serializer = ComentarioBlogSerializer(page, many=True, context={"request": request})
            return paginator.get_paginated_response(serializer.data)
        
        # Si no hay paginación, devolver todos los resultados
        serializer = ComentarioBlogSerializer(comentarios, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
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
    
    📋 FILTRADO POR BLOG:
    - Filtra automáticamente los comentarios según el blogId recibido
    - Mantiene toda la información del autor, contenido, fecha y respuestas
    - Incluye paginación para optimizar la carga de datos
    
    Funcionalidades:
    - 🔍 Búsqueda: ?search=término (busca en el contenido del comentario)
    - 📄 Paginación: usa la configuración global de settings (5 comentarios por página)
    - 🎯 Filtro por blog: ?blog=1 (REQUERIDO para filtrar por blog específico)
    
    Ejemplos de uso:
    - GET /api/v1/blog/comentarios/?blog=1 - Comentarios principales del blog 1
    - GET /api/v1/blog/comentarios/?blog=1&page=2 - Segunda página del blog 1
    - GET /api/v1/blog/comentarios/?blog=1&search=excelente - Buscar en blog 1
    - POST /api/v1/blog/comentarios/ - Crear comentario
    
    Payload para crear comentario:
    {
        "blog": 1,
        "contenido": "Mi comentario aquí",
        "parent": ""  // o ID del comentario padre para respuestas
    }
    
    ✅ LIBERTAD DE COMENTARIOS:
    - Los usuarios pueden comentar MÚLTIPLES veces en cualquier blog
    - Pueden responder a cualquier comentario sin restricciones
    - Fomenta conversaciones dinámicas e interacciones ricas
    
    Respuesta incluye:
    - Información completa del autor (email, usuario_unico)
    - Contenido y fecha de creación
    - Respuestas anidadas con la misma estructura
    - Paginación automática
    """
    serializer_class = ComentarioBlogSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    # Configuración de filtros y búsqueda
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['blog', 'parent']
    search_fields = ['contenido']

    def get_queryset(self):
        """
        Filtra comentarios principales y permite filtrado por blog.
        Optimiza las consultas con select_related para el autor.
        """
        queryset = ComentarioBlog.objects.filter(parent__isnull=True).select_related('autor', 'blog').order_by('-creado_en')
        
        # Filtrar por blog si se proporciona el parámetro
        blog_id = self.request.query_params.get('blog')
        if blog_id:
            queryset = queryset.filter(blog=blog_id)
            
        return queryset

    def perform_create(self, serializer):
        """
        Crear comentario asociado al usuario autenticado.
        
        ✅ PERMITIDO: Los usuarios pueden comentar múltiples veces en blogs.
        Esto fomenta conversaciones e interacciones más dinámicas.
        """
        serializer.save(autor=self.request.user)
