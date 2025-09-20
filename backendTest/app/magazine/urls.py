from rest_framework.routers import DefaultRouter
from .views import EdicionesViewSet, NewsletterViewSet, ContactViewSet

router = DefaultRouter()
router.register(r'editions', EdicionesViewSet, basename="edition")
router.register(r'newsletters', NewsletterViewSet, basename="newsletter")
router.register(r'contacts', ContactViewSet, basename="contact")

urlpatterns = router.urls