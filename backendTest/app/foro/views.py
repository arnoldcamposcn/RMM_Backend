from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from .models import Tema, ComentarioTema, LikeTema
from .serializers import TemaSerializer, ComentarioTemaSerializer, LikeTemaSerializer
from .pagination import TemasPagination
from drf_spectacular.utils import extend_schema


# ----------------------------
# 📌 PERMISOS PERSONALIZADOS
# ----------------------------

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permiso personalizado para permitir solo a los propietarios editar sus objetos.
    """
    def has_object_permission(self, request, view, obj):
        # Permisos de lectura para cualquier request
        if request.method in permissions.SAFE_METHODS:
            return True
        # Permisos de escritura solo para el propietario del objeto
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
    ViewSet para listar, crear, ver detalle, actualizar y eliminar temas del foro.
    
    Permisos:
    - 👀 Lectura: Todos pueden ver temas
    - ✍️ Crear: Solo usuarios autenticados
    - ✏️ Editar: Solo el autor del tema
    - 🗑️ Eliminar: Solo el autor del tema
    
    Funcionalidades:
    - 🔍 Búsqueda: ?search=término (busca en título y contenido)
    - 📄 Paginación: 8 temas por página (?page=1, ?page_size=15)
    
    Ejemplos de uso:
    - GET /api/v1/foro/temas/?search=ayuda
    - GET /api/v1/foro/temas/?page=2&page_size=10
    - POST /api/v1/foro/temas/ - Crear tema
    - PUT /api/v1/foro/temas/1/ - Editar tema (solo autor)
    - DELETE /api/v1/foro/temas/1/ - Eliminar tema (solo autor)
    """
    queryset = Tema.objects.all().order_by("-creado_en")
    serializer_class = TemaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    pagination_class = TemasPagination
    
    # Configuración de búsqueda
    filter_backends = [filters.SearchFilter]
    search_fields = ['titulo', 'contenido']

    def perform_create(self, serializer):
        """Crear tema asociado al usuario autenticado"""
        serializer.save(autor=self.request.user)

    @extend_schema(
        tags=["Foro - Reacciones"],
        description="Dar o quitar 'me gusta' a un tema del foro."
    )
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def toggle_like(self, request, pk=None):
        """
        Acción para dar o quitar 'like' a un tema del foro.
        
        Comportamiento:
        - Si no ha dado like -> Se crea el like
        - Si ya dio like -> Se elimina el like
        
        No requiere payload, solo POST vacío.
        """
        tema = get_object_or_404(Tema, pk=pk)
        user = request.user

        # Verificar si ya existe un like del usuario
        like_obj = LikeTema.objects.filter(tema=tema, usuario=user).first()

        if like_obj:
            # Si existe, eliminarlo (quitar like)
            like_obj.delete()
            liked = False
            message = "👍 Like eliminado"
        else:
            # Si no existe, crearlo (dar like)
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


# ----------------------------
# 📌 COMENTARIOS
# ----------------------------
@extend_schema(
    tags=["Foro - Comentarios"],
    description="Endpoints para consultar y crear comentarios con paginación y búsqueda."
)
class ComentarioTemaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para listar, crear, actualizar y eliminar comentarios de temas del foro.
    
    ⚠️ IMPORTANTE: Solo muestra comentarios principales (sin parent).
    Las respuestas aparecen anidadas en el campo 'respuestas' de cada comentario padre.
    
    Permisos:
    - 👀 Lectura: Todos pueden ver comentarios
    - ✍️ Crear: Solo usuarios autenticados
    - ✏️ Editar: Solo el autor del comentario
    - 🗑️ Eliminar: Solo el autor del comentario
    
    Funcionalidades:
    - 🔍 Búsqueda: ?search=término (busca en el contenido del comentario)
    - 📄 Paginación: usa la configuración global de settings (5 comentarios por página)
    - 🎯 Filtro por tema: ?tema=1
    
    Ejemplos de uso:
    - GET /api/v1/foro/comentarios/?tema=1 - Comentarios principales del tema 1
    - POST /api/v1/foro/comentarios/ - Crear comentario
    
    Payload para crear comentario:
    {
        "tema": 1,
        "contenido": "Mi comentario aquí",
        "parent": ""  // o ID del comentario padre para respuestas
    }
    """
    queryset = ComentarioTema.objects.filter(parent__isnull=True).order_by('-creado_en')
    serializer_class = ComentarioTemaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    
    # Configuración de filtros y búsqueda
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['tema', 'parent']
    search_fields = ['contenido']

    def perform_create(self, serializer):
        """Crear comentario asociado al usuario autenticado"""
        serializer.save(autor=self.request.user)
