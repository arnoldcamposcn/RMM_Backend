from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from .models import Tema, ComentarioTema, LikeTema, Categoria_Foro
from .serializers import (
    TemaSerializer, ComentarioTemaSerializer,
    LikeTemaSerializer, CategoriaForoSerializer
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
    
    ⚠️ RESTRICCIÓN DE CREACIÓN:
    - Un usuario solo puede crear UN tema en el foro
    - Esto mantiene la calidad y evita spam de temas
    
    ✅ LIBERTAD DE PARTICIPACIÓN:
    - Todos pueden comentar múltiples veces en cualquier tema
    - Solo el autor puede editar/eliminar su propio tema
    - Sistema de likes para temas
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
        
        ⚠️ RESTRICCIÓN: Un usuario solo puede crear UN tema en el foro.
        Si intenta crear otro tema, se rechaza la solicitud.
        """
        user = self.request.user
        
        # Verificar si el usuario ya creó un tema
        existing_tema = Tema.objects.filter(autor=user).exists()
        
        if existing_tema:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({
                'error': 'Ya has creado un tema anteriormente.',
                'message': 'Solo se permite crear un tema por usuario en el foro.',
                'code': 'DUPLICATE_TEMA'
            })
        
        serializer.save(autor=user)

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


# ----------------------------
# 📌 COMENTARIOS
# ----------------------------
@extend_schema(
    tags=["Foro - Comentarios"],
    description="Endpoints para consultar y crear comentarios en temas del foro."
)
class ComentarioTemaViewSet(viewsets.ModelViewSet):
    queryset = ComentarioTema.objects.filter(parent__isnull=True).order_by('-creado_en')
    serializer_class = ComentarioTemaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["tema", "parent"]
    search_fields = ["contenido"]

    def perform_create(self, serializer):
        """
        Crear comentario asociado al usuario autenticado.
        
        ✅ PERMITIDO: Los usuarios pueden comentar múltiples veces en temas.
        Esto fomenta conversaciones e interacciones más dinámicas en el foro.
        """
        serializer.save(autor=self.request.user)


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
