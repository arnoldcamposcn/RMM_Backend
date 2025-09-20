from django.urls import path
from .views import MeView, LogoutView, RegistroInicialView, CustomTokenObtainPairView
from django.urls import include

urlpatterns = [
    path("profile", MeView.as_view(), name="profile"),
    path("auth/logout", LogoutView.as_view(), name="logout"),
    path("auth/registro-inicial", RegistroInicialView.as_view(), name="registro-inicial"),
    path("auth/login", CustomTokenObtainPairView.as_view(), name="login"),
    # path("magazine/", include("app.magazine.urls")),
]


# 🔐 AUTENTICACIÓN:
# - POST /users/auth/registro/
# - POST /users/auth/login/
# - POST /users/auth/logout/
# - POST /users/auth/refresh/