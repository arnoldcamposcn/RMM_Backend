from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from .models import Tema, ComentarioTema, LikeTema, LikeComentarioTema, Categoria_Foro
from .serializers import (
    TemaSerializer, ComentarioTemaSerializer,
    LikeTemaSerializer, LikeComentarioTemaSerializer, CategoriaForoSerializer
)
from .pagination import TemasPagination


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.autor == request.user


# ----------------------------
# 📌 TEMAS DEL FORO
# ----------------------------
@extend_schema(
    tags=["Foro - Temas"],
    description="Endpoints para consultar y crear temas en el foro con paginación y búsqueda."
)
class TemaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para listar, crear, actualizar y eliminar temas del foro.
    
    ✅ LIBERTAD TOTAL DE PARTICIPACIÓN:
    - Los usuarios pueden crear MÚLTIPLES temas en el foro
    - Todos pueden comentar múltiples veces en cualquier tema
    - Solo el autor puede editar/eliminar su propio tema
    - Sistema de likes para temas
    - Fomenta la participación activa y diversidad de contenido
    """
    queryset = Tema.objects.all().order_by("-creado_en")
    serializer_class = TemaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    pagination_class = TemasPagination

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["categoria_foro"]
    search_fields = ["titulo", "contenido"]

    def perform_create(self, serializer):
        """
        Crear tema asociado al usuario autenticado.
        
        ✅ LIBERTAD TOTAL: Los usuarios pueden crear múltiples temas en el foro.
        Esto fomenta la participación activa y diversidad de contenido.
        """
        serializer.save(autor=self.request.user)

    @extend_schema(
        tags=["Foro - Reacciones"],
        description="Dar o quitar 'me gusta' a un tema del foro."
    )
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def toggle_like(self, request, pk=None):
        """
        Acción para dar o quitar 'like' a un tema del foro.
        
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
        tema = get_object_or_404(Tema, pk=pk)
        user = request.user
        
        # Obtener la acción solicitada
        action = request.data.get('action', None)
        
        # Verificar el estado actual del like
        like_obj = LikeTema.objects.filter(tema=tema, usuario=user).first()
        has_like = bool(like_obj)

        # Si se especifica una acción, validar estrictamente
        if action == "add":
            if has_like:
                # Ya tiene like, no puede dar like otra vez
                return Response(
                    {
                        "error": "Like duplicado",
                        "message": "Ya has dado like a este tema anteriormente.",
                        "code": "DUPLICATE_LIKE",
                        "tema": tema.id,
                        "usuario": user.id,
                        "liked": True,
                        "likes_count": tema.likes.count()
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                # No tiene like, crear uno nuevo
                LikeTema.objects.create(tema=tema, usuario=user)
                return Response(
                    {
                        "tema": tema.id,
                        "usuario": user.id,
                        "liked": True,
                        "likes_count": tema.likes.count(),
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
                        "message": "No has dado like a este tema anteriormente.",
                        "code": "LIKE_NOT_FOUND",
                        "tema": tema.id,
                        "usuario": user.id,
                        "liked": False,
                        "likes_count": tema.likes.count()
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                # Tiene like, eliminarlo
                like_obj.delete()
                return Response(
                    {
                        "tema": tema.id,
                        "usuario": user.id,
                        "liked": False,
                        "likes_count": tema.likes.count(),
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
                LikeTema.objects.create(tema=tema, usuario=user)
                liked = True
                message = "👍 Like agregado"

            return Response(
                {
                    "tema": tema.id,
                    "usuario": user.id,
                    "liked": liked,
                    "likes_count": tema.likes.count(),
                    "message": message
                },
                status=status.HTTP_200_OK
            )

    @extend_schema(
        tags=["Foro - Reacciones"],
        description="Obtener lista de usuarios que dieron like a un tema específico."
    )
    @action(detail=True, methods=["get"], permission_classes=[permissions.AllowAny])
    def likes_list(self, request, pk=None):
        """
        Endpoint para obtener la lista de usuarios que dieron like a un tema específico.
        
        Permite al frontend:
        - Validar si el usuario autenticado está en la lista
        - Mostrar el corazón en rojo si ya dio like
        - Obtener información de todos los usuarios que dieron like
        
        Respuesta incluye:
        - Lista de usuarios con información básica (id, email, usuario_unico)
        - Total de likes
        - Estado del usuario autenticado (si está logueado)
        """
        tema = get_object_or_404(Tema, pk=pk)
        
        # Obtener todos los likes del tema
        likes = LikeTema.objects.filter(tema=tema).select_related('usuario').order_by('-creado_en')
        
        # Serializar la información de los usuarios
        from .serializers import LikeTemaSerializer
        likes_data = LikeTemaSerializer(likes, many=True).data
        
        # Información del usuario autenticado si está logueado
        user_liked = False
        user_info = None
        
        if request.user.is_authenticated:
            user_like = LikeTema.objects.filter(tema=tema, usuario=request.user).first()
            user_liked = bool(user_like)
            user_info = {
                "id": request.user.id,
                "email": request.user.email,
                "usuario_unico": request.user.usuario_unico,
                "liked": user_liked
            }
        
        return Response(
            {
                "tema": {
                    "id": tema.id,
                    "titulo": tema.titulo,
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
        tags=["Foro - Comentarios"],
        description="Lista todos los comentarios principales de un tema específico con paginación."
    )
    @action(detail=True, methods=["get"], permission_classes=[permissions.AllowAny])
    def comentarios(self, request, pk=None):
        """
        Endpoint dedicado para traer SOLO los comentarios principales de un tema.
        Incluye paginación y respuestas anidadas.
        
        Parámetros de consulta:
        - page: Número de página (ej: ?page=2)
        - page_size: Cantidad por página (ej: ?page_size=10)
        - search: Buscar en contenido (ej: ?search=excelente)
        """
        tema = get_object_or_404(Tema, pk=pk)
        
        # Obtener comentarios principales del tema
        comentarios = ComentarioTema.objects.filter(
            tema=tema, 
            parent__isnull=True
        ).select_related('autor').order_by('-creado_en')
        
        # Aplicar búsqueda si se proporciona
        search = request.query_params.get('search')
        if search:
            comentarios = comentarios.filter(contenido__icontains=search)
        
        # Aplicar paginación
        paginator = TemasPagination()
        page = paginator.paginate_queryset(comentarios, request, view=self)
        
        if page is not None:
            serializer = ComentarioTemaSerializer(page, many=True, context={"request": request})
            return paginator.get_paginated_response(serializer.data)
        
        # Si no hay paginación, devolver todos los resultados
        serializer = ComentarioTemaSerializer(comentarios, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


# ----------------------------
# 📌 COMENTARIOS
# ----------------------------
@extend_schema(
    tags=["Foro - Comentarios"],
    description="Endpoints para consultar y crear comentarios en temas del foro."
)
class ComentarioTemaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para listar, crear, actualizar y eliminar comentarios de temas del foro.
    
    ⚠️ IMPORTANTE: Solo muestra comentarios principales (sin parent).
    Las respuestas aparecen anidadas en el campo 'respuestas' de cada comentario padre.
    
    📋 FILTRADO POR TEMA:
    - Filtra automáticamente los comentarios según el temaId recibido
    - Mantiene toda la información del autor, contenido, fecha y respuestas
    - Incluye paginación para optimizar la carga de datos
    
    Funcionalidades:
    - 🔍 Búsqueda: ?search=término (busca en el contenido del comentario)
    - 📄 Paginación: usa la configuración global de settings (5 comentarios por página)
    - 🎯 Filtro por tema: ?tema=1 (REQUERIDO para filtrar por tema específico)
    
    Ejemplos de uso:
    - GET /api/v1/foro/comentarios/?tema=1 - Comentarios principales del tema 1
    - GET /api/v1/foro/comentarios/?tema=1&page=2 - Segunda página del tema 1
    - GET /api/v1/foro/comentarios/?tema=1&search=excelente - Buscar en tema 1
    - POST /api/v1/foro/comentarios/ - Crear comentario
    
    Payload para crear comentario:
    {
        "tema": 1,
        "contenido": "Mi comentario aquí",
        "parent": ""  // o ID del comentario padre para respuestas
    }
    
    ✅ LIBERTAD DE COMENTARIOS:
    - Los usuarios pueden comentar MÚLTIPLES veces en cualquier tema
    - Pueden responder a cualquier comentario sin restricciones
    - Fomenta conversaciones dinámicas e interacciones ricas
    
    Respuesta incluye:
    - Información completa del autor (email, usuario_unico)
    - Contenido y fecha de creación
    - Respuestas anidadas con la misma estructura
    - Paginación automática
    """
    serializer_class = ComentarioTemaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    # Configuración de filtros y búsqueda
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["tema", "parent"]
    search_fields = ["contenido"]

    def get_queryset(self):
        """
        Filtra comentarios principales y permite filtrado por tema.
        Optimiza las consultas con select_related para el autor.
        """
        queryset = ComentarioTema.objects.filter(parent__isnull=True).select_related('autor', 'tema').order_by('-creado_en')
        
        # Filtrar por tema si se proporciona el parámetro
        tema_id = self.request.query_params.get('tema')
        if tema_id:
            queryset = queryset.filter(tema=tema_id)
            
        return queryset

    def perform_create(self, serializer):
        """
        Crear comentario asociado al usuario autenticado.
        
        ✅ PERMITIDO: Los usuarios pueden comentar múltiples veces en temas.
        Esto fomenta conversaciones e interacciones más dinámicas en el foro.
        """
        serializer.save(autor=self.request.user)

    @extend_schema(
        tags=["Foro - Comentarios - Reacciones"],
        description="Dar o quitar 'me gusta' a un comentario específico del foro."
    )
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def toggle_like(self, request, pk=None):
        """
        Acción para dar o quitar 'like' a un comentario específico del foro.
        
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
        comentario = get_object_or_404(ComentarioTema, pk=pk)
        user = request.user
        
        # Obtener la acción solicitada
        action = request.data.get('action', None)
        
        # Verificar el estado actual del like
        like_obj = LikeComentarioTema.objects.filter(comentario=comentario, usuario=user).first()
        has_like = bool(like_obj)

        # Si se especifica una acción, validar estrictamente
        if action == "add":
            if has_like:
                # Ya tiene like, no puede dar like otra vez
                return Response(
                    {
                        "error": "Like duplicado",
                        "message": "Ya has dado like a este comentario anteriormente.",
                        "code": "DUPLICATE_LIKE",
                        "comentario": comentario.id,
                        "usuario": user.id,
                        "liked": True,
                        "likes_count": comentario.likes.count()
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                # No tiene like, crear uno nuevo
                LikeComentarioTema.objects.create(comentario=comentario, usuario=user)
                return Response(
                    {
                        "comentario": comentario.id,
                        "usuario": user.id,
                        "liked": True,
                        "likes_count": comentario.likes.count(),
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
                        "message": "No has dado like a este comentario anteriormente.",
                        "code": "LIKE_NOT_FOUND",
                        "comentario": comentario.id,
                        "usuario": user.id,
                        "liked": False,
                        "likes_count": comentario.likes.count()
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                # Tiene like, eliminarlo
                like_obj.delete()
                return Response(
                    {
                        "comentario": comentario.id,
                        "usuario": user.id,
                        "liked": False,
                        "likes_count": comentario.likes.count(),
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
                LikeComentarioTema.objects.create(comentario=comentario, usuario=user)
                liked = True
                message = "👍 Like agregado"

            return Response(
                {
                    "comentario": comentario.id,
                    "usuario": user.id,
                    "liked": liked,
                    "likes_count": comentario.likes.count(),
                    "message": message
                },
                status=status.HTTP_200_OK
            )

    @extend_schema(
        tags=["Foro - Comentarios - Reacciones"],
        description="Obtener lista de usuarios que dieron like a un comentario específico."
    )
    @action(detail=True, methods=["get"], permission_classes=[permissions.AllowAny])
    def likes_list(self, request, pk=None):
        """
        Endpoint para obtener la lista de usuarios que dieron like a un comentario específico.
        
        Permite al frontend:
        - Validar si el usuario autenticado está en la lista
        - Mostrar el corazón en rojo si ya dio like al comentario
        - Obtener información de todos los usuarios que dieron like
        """
        comentario = get_object_or_404(ComentarioTema, pk=pk)
        
        # Obtener todos los likes del comentario
        likes = LikeComentarioTema.objects.filter(comentario=comentario).select_related('usuario').order_by('-creado_en')
        
        # Serializar la información de los usuarios
        likes_data = LikeComentarioTemaSerializer(likes, many=True).data
        
        # Información del usuario autenticado si está logueado
        user_liked = False
        user_info = None
        
        if request.user.is_authenticated:
            user_like = LikeComentarioTema.objects.filter(comentario=comentario, usuario=request.user).first()
            user_liked = bool(user_like)
            user_info = {
                "id": request.user.id,
                "email": request.user.email,
                "usuario_unico": request.user.usuario_unico,
                "liked": user_liked
            }
        
        return Response(
            {
                "comentario": {
                    "id": comentario.id,
                    "contenido": comentario.contenido[:50] + "..." if len(comentario.contenido) > 50 else comentario.contenido,
                    "tema": comentario.tema.id,
                    "likes_count": likes.count()
                },
                "likes_list": likes_data,
                "current_user": user_info,
                "user_liked": user_liked,
                "total_likes": likes.count()
            },
            status=status.HTTP_200_OK
        )


# ----------------------------
# 📌 CATEGORÍAS DEL FORO
# ----------------------------
@extend_schema(
    tags=["Foro - Categorías"],
    description="Endpoints para listar categorías disponibles del foro."
)
class CategoriaForoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Categoria_Foro.objects.all().order_by("nombre_categoria")
    serializer_class = CategoriaForoSerializer
    permission_classes = [permissions.AllowAny]
