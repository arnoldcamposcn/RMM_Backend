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
from app.common.filters import AccentInsensitiveSearchFilter
from app.common.permissions import CanManageContent, CanComment, CanLike

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
class BlogViewSet(viewsets.ModelViewSet):
    """
    ViewSet SOLO DE LECTURA para listar y ver detalles de blogs.

    ⚠️ IMPORTANTE: Los blogs solo pueden ser creados/editados por administradores
    desde el Django Admin Panel.

    Funcionalidades:
    - 🔍 Búsqueda: ?search=término (busca en título y contenido)
      ✨ NUEVO: La búsqueda ignora acentos y diacríticos
      - Buscar "noticia" encontrará "noticia" y "noticias"
      - Buscar "tecnología" encontrará "tecnologia" y "tecnología"
    - 📄 Paginación: 5 blogs por página (?page=1, ?page_size=10)
    - 👁️ Solo lectura: GET /list/ y GET /detail/ disponibles
    - 📌 Cada blog incluye su categoría, artículos relacionados, comentarios y likes

    Ejemplos de uso:
    - GET /api/v1/blog/?search=django
    - GET /api/v1/blog/?search=tecnologia (encuentra "tecnología")
    - GET /api/v1/blog/?page=2&page_size=10
    - GET /api/v1/blog/1/ (detalle específico con artículos y comentarios)
    """
    queryset = Blog.objects.all().order_by('-fecha_publicacion')
    serializer_class = BlogSerializer
    permission_classes = [CanManageContent]  # Lectura: Todos | Escritura: Admin/Superusuario
    pagination_class = BlogPagination

    # Configuración de búsqueda (con soporte para búsqueda sin acentos)
    filter_backends = [AccentInsensitiveSearchFilter]
    search_fields = ['titulo_blog', 'contenido']

    @extend_schema(
        tags=["Blogs - Reacciones"],
        description="Dar o quitar 'me gusta' a un blog."
    )
    @action(detail=True, methods=["post"], permission_classes=[CanLike])
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

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

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
        tags=["Blogs - Artículos"],
        description="Gestiona los artículos asociados a un blog específico."
    )
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def manage_articulos(self, request, pk=None):
        """
        Endpoint para gestionar artículos de un blog.
        
        Permite:
        - Agregar artículos: {"action": "add", "articulos_ids": [1, 2, 3]}
        - Remover artículos: {"action": "remove", "articulos_ids": [1, 2]}
        - Reemplazar todos: {"action": "set", "articulos_ids": [1, 2, 3]}
        - Limpiar todos: {"action": "clear"}
        """
        blog = get_object_or_404(Blog, pk=pk)
        action = request.data.get('action')
        articulos_ids = request.data.get('articulos_ids', [])
        
        if action == "add":
            # Agregar artículos sin remover los existentes
            from app.articles.models import Articulos
            articulos = Articulos.objects.filter(id__in=articulos_ids)
            blog.articulos.add(*articulos)
            message = f"Artículos {articulos_ids} agregados al blog"
            
        elif action == "remove":
            # Remover artículos específicos
            from app.articles.models import Articulos
            articulos = Articulos.objects.filter(id__in=articulos_ids)
            blog.articulos.remove(*articulos)
            message = f"Artículos {articulos_ids} removidos del blog"
            
        elif action == "set":
            # Reemplazar todos los artículos
            from app.articles.models import Articulos
            articulos = Articulos.objects.filter(id__in=articulos_ids)
            blog.articulos.set(articulos)
            message = f"Artículos del blog actualizados: {articulos_ids}"
            
        elif action == "clear":
            # Limpiar todos los artículos
            blog.articulos.clear()
            message = "Todos los artículos removidos del blog"
            
        else:
            return Response(
                {
                    "error": "Acción no válida",
                    "message": "Las acciones válidas son: 'add', 'remove', 'set', 'clear'",
                    "valid_actions": ["add", "remove", "set", "clear"]
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Devolver el blog actualizado con sus artículos
        serializer = BlogSerializer(blog, context={"request": request})
        return Response(
            {
                "message": message,
                "blog": serializer.data,
                "articulos_count": blog.articulos.count()
            },
            status=status.HTTP_200_OK
        )

    @extend_schema(
        tags=["Blogs - Artículos"],
        description="Obtiene artículos disponibles y elegidos para un blog específico."
    )
    @action(detail=True, methods=["get"], permission_classes=[permissions.IsAdminUser])
    def articulos_management(self, request, pk=None):
        """
        Endpoint para obtener la información necesaria para gestionar artículos de un blog.
        
        Útil para crear interfaces tipo Django Admin con:
        - Artículos disponibles (todos los artículos)
        - Artículos elegidos (artículos ya asociados al blog)
        """
        blog = get_object_or_404(Blog, pk=pk)
        
        # Obtener todos los artículos
        from app.articles.models import Articulos
        todos_los_articulos = Articulos.objects.all().order_by('-fecha_publicacion')
        
        # Obtener artículos ya asociados al blog
        articulos_elegidos = blog.articulos.all().order_by('-fecha_publicacion')
        
        # Serializar los artículos
        articulos_disponibles_serializer = ArticuloSerializer(todos_los_articulos, many=True, context={"request": request})
        articulos_elegidos_serializer = ArticuloSerializer(articulos_elegidos, many=True, context={"request": request})
        
        return Response(
            {
                "blog": {
                    "id": blog.id,
                    "titulo_blog": blog.titulo_blog
                },
                "articulos_disponibles": articulos_disponibles_serializer.data,
                "articulos_elegidos": articulos_elegidos_serializer.data,
                "counts": {
                    "disponibles": todos_los_articulos.count(),
                    "elegidos": articulos_elegidos.count()
                }
            },
            status=status.HTTP_200_OK
        )









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
# ==========================
# COMENTARIOS
# ==========================
@extend_schema(tags=["Blogs - Comentarios"], description="CRUD de comentarios (todos los niveles) con búsqueda sin acentos.")
class ComentarioBlogViewSet(viewsets.ModelViewSet):
    serializer_class = ComentarioBlogSerializer
    permission_classes = [CanComment]  # Lectura: Todos | Comentar: Autenticados | Editar: Autor o Admin
    filter_backends = [DjangoFilterBackend, AccentInsensitiveSearchFilter]
    filterset_fields = ['blog', 'parent']
    search_fields = ['contenido']

    def get_queryset(self):
        qs = ComentarioBlog.objects.all().select_related('autor', 'blog').prefetch_related(
            'respuestas__autor', 'respuestas__respuestas__autor'
        ).order_by('-creado_en')

        blog_id = self.request.query_params.get('blog')
        if blog_id:
            qs = qs.filter(blog=blog_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(autor=self.request.user)

    @extend_schema(tags=["Blogs - Comentarios"], description="Lista paginada de respuestas directas de un comentario (1 nivel).")
    @action(detail=True, methods=["get"], permission_classes=[permissions.AllowAny])
    def children(self, request, pk=None):
        comentario = get_object_or_404(ComentarioBlog, pk=pk)
        hijos = comentario.respuestas.all().select_related('autor')

        paginator = BlogPagination()
        page = paginator.paginate_queryset(hijos, request, view=self)
        ser = ComentarioBlogSerializer(page or hijos, many=True, context={"request": request})
        return paginator.get_paginated_response(ser.data) if page is not None else Response(ser.data, status=200)
