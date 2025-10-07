from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ArticuloViewSet, ComentarioArticuloViewSet

# Router para artículos y comentarios
router = DefaultRouter()
router.register("articulos", ArticuloViewSet, basename="articulos")
router.register("comentarios", ComentarioArticuloViewSet, basename="comentarios")

urlpatterns = router.urls
