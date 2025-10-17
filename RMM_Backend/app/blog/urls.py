from rest_framework.routers import DefaultRouter
from .views import BlogViewSet, ComentarioBlogViewSet

router = DefaultRouter()
router.register("noticias", BlogViewSet, basename="blogs")
router.register("comentarios", ComentarioBlogViewSet, basename="comentarios-blogs")

urlpatterns = router.urls
