from django.urls import path
from .views import (
    MeView, LogoutView, RegistroInicialView, CustomTokenObtainPairView, 
    RequestPasswordResetView, ResetPasswordConfirmView,
    AssignRoleView, ListUsersWithRolesView, AdminLoginView
)
from django.urls import include

urlpatterns = [
    path("profile", MeView.as_view(), name="profile"),
    path("auth/logout", LogoutView.as_view(), name="logout"),
    path("auth/registro-inicial", RegistroInicialView.as_view(), name="registro-inicial"),
    path("auth/login", CustomTokenObtainPairView.as_view(), name="login"),
    path("auth/login-admin", AdminLoginView.as_view(), name="login-admin"),  # Login exclusivo para Admin/Superusuario

    # Endpoints de recuperación de contraseña
    path("auth/request-password-reset/", RequestPasswordResetView.as_view(), name="request_password_reset"),
    path("auth/reset-password-confirm/", ResetPasswordConfirmView.as_view(), name="reset_password_confirm"),
    
    # Endpoints de gestión de roles (solo Superusuario)
    path("roles/assign/", AssignRoleView.as_view(), name="assign_role"),
    path("roles/users/", ListUsersWithRolesView.as_view(), name="list_users_with_roles"),

]


# 🔐 AUTENTICACIÓN:
# - POST /users/auth/registro-inicial/ - Registro inicial de usuario
# - POST /users/auth/login/ - Iniciar sesión (Todos los usuarios)
# - POST /users/auth/login-admin/ - Iniciar sesión en panel admin (Solo Admin/Superusuario)
# - POST /users/auth/logout/ - Cerrar sesión
# - GET /users/profile/ - Obtener perfil del usuario autenticado
# - POST /users/auth/request-password-reset/ - Solicitar recuperación de contraseña
# - POST /users/auth/reset-password-confirm/ - Confirmar nueva contraseña

# 👑 GESTIÓN DE ROLES (Solo Superusuario):
# - POST /users/roles/assign/ - Asignar rol a un usuario
# - GET /users/roles/users/ - Listar todos los usuarios con sus roles