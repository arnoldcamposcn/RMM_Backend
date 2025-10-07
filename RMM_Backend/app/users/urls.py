from django.urls import path
from .views import MeView, LogoutView, RegistroInicialView, CustomTokenObtainPairView, RequestPasswordResetView, ResetPasswordConfirmView
from django.urls import include

urlpatterns = [
    path("profile", MeView.as_view(), name="profile"),
    path("auth/logout", LogoutView.as_view(), name="logout"),
    path("auth/registro-inicial", RegistroInicialView.as_view(), name="registro-inicial"),
    path("auth/login", CustomTokenObtainPairView.as_view(), name="login"),

    # Endpoints de recuperación de contraseña
    path("auth/request-password-reset/", RequestPasswordResetView.as_view(), name="request_password_reset"),
    path("auth/reset-password-confirm/", ResetPasswordConfirmView.as_view(), name="reset_password_confirm"),
    

]


# 🔐 AUTENTICACIÓN:
# - POST /users/auth/registro-inicial/ - Registro inicial de usuario
# - POST /users/auth/login/ - Iniciar sesión
# - POST /users/auth/logout/ - Cerrar sesión
# - GET /users/profile/ - Obtener perfil del usuario autenticado
# - POST /users/auth/request-password-reset/ - Solicitar recuperación de contraseña
# - POST /users/auth/reset-password-confirm/ - Confirmar nueva contraseña