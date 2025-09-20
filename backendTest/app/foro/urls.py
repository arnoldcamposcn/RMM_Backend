from rest_framework.routers import DefaultRouter
from .views import TemaViewSet, ComentarioTemaViewSet

router = DefaultRouter()
router.register(r"temas", TemaViewSet, basename="temas")
router.register(r"comentarios", ComentarioTemaViewSet, basename="comentarios")

urlpatterns = router.urls
