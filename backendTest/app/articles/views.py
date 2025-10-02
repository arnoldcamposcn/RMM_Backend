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
class ArticuloViewSet(viewsets.ModelViewSet):
    """
    ViewSet SOLO DE LECTURA para listar y ver detalles de artículos.
    
    ⚠️ IMPORTANTE: Los artículos solo pueden ser creados/editados por administradores
    desde el Django Admin Panel.
    
    Funcionalidades:
    - 🔍 Búsqueda: ?search=término (busca en título y contenido)
    - 🏷️ Filtrado: ?categoria_articulo=1 (filtra por categoría)
    - 📄 Paginación: 6 artículos por página (?page=1, ?page_size=10)
    - 👁️ Solo lectura: GET /list/ y GET /detail/ disponibles
    
    Ejemplos de uso:
    - GET /api/v1/articles/?search=tecnología
    - GET /api/v1/articles/?categoria_articulo=1 (filtrar por categoría)
    - GET /api/v1/articles/?search=python&categoria_articulo=2 (buscar y filtrar)
    - GET /api/v1/articles/?page=2&page_size=10
    - GET /api/v1/articles/1/ (detalle específico)
    - GET /api/v1/articles/categorias/ (listar categorías disponibles)
    """
    queryset = Articulos.objects.select_related('categoria_articulo').order_by('-fecha_publicacion')
    serializer_class = ArticuloSerializer
    permission_classes = [permissions.AllowAny]  # Solo lectura, acceso público
    pagination_class = ArticulosPagination
    
    # Configuración de filtros y búsqueda
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['categoria_articulo']
    search_fields = ['titulo_articulo', 'contenido']

    @extend_schema(
        tags=["Artículos - Reacciones"],
        description="Dar o quitar 'me gusta' a un artículo."
    )
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def toggle_like(self, request, pk=None):
        """
        Acción para dar o quitar 'like' a un artículo completo.
        
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
        articulo = get_object_or_404(Articulos, pk=pk)
        user = request.user
        
        # Obtener la acción solicitada
        action = request.data.get('action', None)
        
        # Verificar el estado actual del like
        like_obj = LikeArticulo.objects.filter(articulo=articulo, usuario=user).first()
        has_like = bool(like_obj)

        # Si se especifica una acción, validar estrictamente
        if action == "add":
            if has_like:
                # Ya tiene like, no puede dar like otra vez
                return Response(
                    {
                        "error": "Like duplicado",
                        "message": "Ya has dado like a este artículo anteriormente.",
                        "code": "DUPLICATE_LIKE",
                        "articulo": articulo.id,
                        "usuario": user.id,
                        "liked": True,
                        "likes_count": articulo.likes.count()
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                # No tiene like, crear uno nuevo
                LikeArticulo.objects.create(articulo=articulo, usuario=user)
                return Response(
                    {
                        "articulo": articulo.id,
                        "usuario": user.id,
                        "liked": True,
                        "likes_count": articulo.likes.count(),
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
                        "message": "No has dado like a este artículo anteriormente.",
                        "code": "LIKE_NOT_FOUND",
                        "articulo": articulo.id,
                        "usuario": user.id,
                        "liked": False,
                        "likes_count": articulo.likes.count()
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                # Tiene like, eliminarlo
                like_obj.delete()
                return Response(
                    {
                        "articulo": articulo.id,
                        "usuario": user.id,
                        "liked": False,
                        "likes_count": articulo.likes.count(),
                        "message": "👍 Like eliminado exitosamente"
                    },
                    status=status.HTTP_200_OK
                )
        
        # Si no se especifica action, comportamiento toggle (para compatibilidad)
        else:
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
            
    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]


    @extend_schema(
        tags=["Artículos - Reacciones"],
        description="Obtener lista de usuarios que dieron like a un artículo específico."
    )
    @action(detail=True, methods=["get"], permission_classes=[permissions.AllowAny])
    def likes_list(self, request, pk=None):
        """
        Endpoint para obtener la lista de usuarios que dieron like a un artículo específico.
        
        Permite al frontend:
        - Validar si el usuario autenticado está en la lista
        - Mostrar el corazón en rojo si ya dio like
        - Obtener información de todos los usuarios que dieron like
        
        Respuesta incluye:
        - Lista de usuarios con información básica (id, email, usuario_unico)
        - Total de likes
        - Estado del usuario autenticado (si está logueado)
        """
        articulo = get_object_or_404(Articulos, pk=pk)
        
        # Obtener todos los likes del artículo
        likes = LikeArticulo.objects.filter(articulo=articulo).select_related('usuario').order_by('-creado_en')
        
        # Serializar la información de los usuarios
        from .serializers import LikeArticuloSerializer
        likes_data = LikeArticuloSerializer(likes, many=True).data
        
        # Información del usuario autenticado si está logueado
        user_liked = False
        user_info = None
        
        if request.user.is_authenticated:
            user_like = LikeArticulo.objects.filter(articulo=articulo, usuario=request.user).first()
            user_liked = bool(user_like)
            user_info = {
                "id": request.user.id,
                "email": request.user.email,
                "usuario_unico": request.user.usuario_unico,
                "liked": user_liked
            }
        
        return Response(
            {
                "articulo": {
                    "id": articulo.id,
                    "titulo": articulo.titulo_articulo,
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
        tags=["Artículos - Comentarios"],
        description="Lista todos los comentarios principales de un artículo específico con paginación."
    )
    @action(detail=True, methods=["get"], permission_classes=[permissions.AllowAny])
    def comentarios(self, request, pk=None):
        """
        Endpoint dedicado para traer SOLO los comentarios principales de un artículo.
        Incluye paginación y respuestas anidadas.
        
        Parámetros de consulta:
        - page: Número de página (ej: ?page=2)
        - page_size: Cantidad por página (ej: ?page_size=10)
        - search: Buscar en contenido (ej: ?search=excelente)
        """
        articulo = get_object_or_404(Articulos, pk=pk)
        
        # Obtener comentarios principales del artículo
        comentarios = ComentarioArticulo.objects.filter(
            articulo=articulo, 
            parent__isnull=True
        ).select_related('autor').order_by('-creado_en')
        
        # Aplicar búsqueda si se proporciona
        search = request.query_params.get('search')
        if search:
            comentarios = comentarios.filter(contenido__icontains=search)
        
        # Aplicar paginación
        paginator = ArticulosPagination()
        page = paginator.paginate_queryset(comentarios, request, view=self)
        
        if page is not None:
            serializer = ComentarioArticuloSerializer(page, many=True, context={"request": request})
            return paginator.get_paginated_response(serializer.data)
        
        # Si no hay paginación, devolver todos los resultados
        serializer = ComentarioArticuloSerializer(comentarios, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Artículos - Categorías"],
        description="Obtener lista de todas las categorías disponibles para artículos."
    )
    @action(detail=False, methods=["get"], permission_classes=[permissions.AllowAny])
    def categorias(self, request):
        """
        Endpoint para obtener todas las categorías disponibles para artículos.
        
        Útil para:
        - Mostrar opciones de filtrado en el frontend
        - Crear formularios de selección de categoría
        - Validar categorías existentes
        
        Respuesta incluye:
        - Lista completa de categorías
        - Total de artículos por categoría
        - Información de slug para URLs amigables
        """
        from app.blog.models import Categoria_Blog
        from .serializers import CategoriaArticuloSerializer
        
        # Obtener todas las categorías con conteo de artículos
        categorias = Categoria_Blog.objects.all().order_by('nombre_categoria')
        
        # Serializar las categorías
        serializer = CategoriaArticuloSerializer(categorias, many=True)
        
        # Agregar información adicional (conteo de artículos por categoría)
        categorias_data = []
        for categoria_data in serializer.data:
            categoria = Categoria_Blog.objects.get(id=categoria_data['id'])
            categoria_info = categoria_data.copy()
            categoria_info['total_articulos'] = categoria.articulos.count()
            categorias_data.append(categoria_info)
        
        return Response(
            {
                "categorias": categorias_data,
                "total_categorias": categorias.count(),
                "info": "Categorías disponibles para filtrar artículos"
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
    
    📋 FILTRADO POR ARTÍCULO:
    - Filtra automáticamente los comentarios según el articuloId recibido
    - Mantiene toda la información del autor, contenido, fecha y respuestas
    - Incluye paginación para optimizar la carga de datos
    
    Funcionalidades:
    - 🔍 Búsqueda: ?search=término (busca en el contenido del comentario)
    - 📄 Paginación: usa la configuración global de settings (5 comentarios por página)
    - 🎯 Filtro por artículo: ?articulo=1 (REQUERIDO para filtrar por artículo específico)
    
    Ejemplos de uso:
    - GET /api/v1/articles/comentarios/?articulo=1 - Comentarios principales del artículo 1
    - GET /api/v1/articles/comentarios/?articulo=1&page=2 - Segunda página del artículo 1
    - GET /api/v1/articles/comentarios/?articulo=1&search=excelente - Buscar en artículo 1
    - POST /api/v1/articles/comentarios/ - Crear comentario
    
    Payload para crear comentario:
    {
        "articulo": 1,
        "contenido": "Mi comentario aquí",
        "parent": ""  // o ID del comentario padre para respuestas
    }
    
    ✅ LIBERTAD DE COMENTARIOS:
    - Los usuarios pueden comentar MÚLTIPLES veces en cualquier artículo
    - Pueden responder a cualquier comentario sin restricciones
    - Fomenta conversaciones dinámicas e interacciones ricas
    
    Respuesta incluye:
    - Información completa del autor (email, usuario_unico)
    - Contenido y fecha de creación
    - Respuestas anidadas con la misma estructura
    - Paginación automática
    """
    serializer_class = ComentarioArticuloSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    # Configuración de filtros y búsqueda
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['articulo', 'parent']
    search_fields = ['contenido']

    def get_queryset(self):
        qs = ComentarioArticulo.objects.all().select_related('autor', 'articulo').prefetch_related(
            'respuestas__autor', 
            'respuestas__respuestas__autor',
            'respuestas__respuestas__respuestas__autor',
            'respuestas__respuestas__respuestas__respuestas__autor'
        ).order_by('-creado_en')

        articulo_id = self.request.query_params.get('articulo')
        if articulo_id:
            qs = qs.filter(articulo=articulo_id)
        return qs


    def perform_create(self, serializer):
        serializer.save(autor=self.request.user)


    @extend_schema(
        tags=["Artículos - Comentarios"],
        description="Lista todos los comentarios principales de un artículo específico con paginación."
    )
    @action(detail=True, methods=["get"], permission_classes=[permissions.AllowAny])
    def children(self, request, pk=None):
        comentario = get_object_or_404(ComentarioArticulo, pk=pk)
        hijos = comentario.respuestas.all().select_related('autor')
        
        paginator = ArticulosPagination()
        page = paginator.paginate_queryset(hijos, request, view=self)
        ser = ComentarioArticuloSerializer(page or hijos, many=True, context={"request": request})
        return paginator.get_paginated_response(ser.data) if page is not None else Response(ser.data, status=200)
