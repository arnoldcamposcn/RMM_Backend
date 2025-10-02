from rest_framework import viewsets, permissions, filters, mixins
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import Ediciones, Newsletter, Contacto
from .serializers import EdicionesSerializer, NewsletterSerializer, ContactSerializer
from .pagination import WeeklyEditionPagination

# ----------------------------
# 📌 EDICIONES
# ----------------------------
@extend_schema(
    tags=["Ediciones"],
    description="Endpoints para consultar las ediciones de la revista."
)
class EdicionesViewSet(viewsets.ModelViewSet):
    queryset = Ediciones.objects.all()
    serializer_class = EdicionesSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = WeeklyEditionPagination

    # 👇 Importante: activar búsqueda y filtros
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['titulo_edicion', 'contenido']
    filterset_fields = ['fecha_publicacion']

    @extend_schema(
        summary="Obtener la última edición",
        description="Devuelve la edición más reciente publicada."
    )
    @action(detail=False, methods=['get'])
    def last(self, request):
        edicion = Ediciones.objects.order_by('-fecha_publicacion').first()
        if not edicion:
            return Response({"detail": "No hay ediciones"})
        return Response(self.get_serializer(edicion).data)

    @extend_schema(
        summary="Obtener ediciones pasadas",
        description="Devuelve todas las ediciones semanales anteriores a la última publicada, con paginación de 5 en 5."
    )
    @action(detail=False, methods=['get'])
    def past(self, request):
        ediciones = Ediciones.objects.order_by('-fecha_publicacion')[1:]
        page = self.paginate_queryset(ediciones)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return Response(self.get_serializer(ediciones, many=True).data)
    
    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]


# ----------------------------
# 📌 NEWSLETTER
# ----------------------------
@extend_schema(
    tags=["Newsletter"],
    description="Endpoints para crear y consultar el newsletter."
)
class NewsletterViewSet(mixins.CreateModelMixin,
                        viewsets.GenericViewSet):
    queryset = Newsletter.objects.all()
    serializer_class = NewsletterSerializer
    permission_classes = [permissions.AllowAny]



# ----------------------------
# 📬 Contacto: solo crear y listar
# ----------------------------
@extend_schema(
    tags=["Contacto"],
    description="Endpoints para crear y consultar el contacto."
)
class ContactViewSet(mixins.CreateModelMixin,
                     viewsets.GenericViewSet):
    queryset = Contacto.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [permissions.AllowAny]