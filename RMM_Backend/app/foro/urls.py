from rest_framework.routers import DefaultRouter
from .views import TemaViewSet, ComentarioTemaViewSet, CategoriaForoViewSet

router = DefaultRouter()
router.register(r"temas", TemaViewSet, basename="temas")
router.register(r"comentarios", ComentarioTemaViewSet, basename="comentarios")
router.register(r"categorias", CategoriaForoViewSet, basename="categorias")

urlpatterns = router.urls
