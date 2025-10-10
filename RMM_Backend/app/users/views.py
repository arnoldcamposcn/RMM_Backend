from rest_framework import generics, permissions, serializers
from django.contrib.auth import logout
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_spectacular.utils import extend_schema, inline_serializer
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from .serializers import RegistroInicialSerializer, UserSimpleSerializer, UserSerializer, CustomTokenObtainPairSerializer, RequestPasswordResetSerializer, ResetPasswordConfirmSerializer
from .models import User
from app.common.permissions import IsSuperusuario
from .pagination import UsersPagination
from app.common.filters import AccentInsensitiveSearchFilter


# ============================================================================
# VIEWS DE PERFIL
# ============================================================================

@extend_schema(
    tags=['Perfil']
)
class MeView(generics.RetrieveUpdateAPIView):
    """
    Vista para que el usuario autenticado vea y actualice su perfil.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Devuelve el usuario autenticado"""
        return self.request.user

    @extend_schema(
        summary="Obtener perfil",
        description="Obtiene los datos del perfil del usuario actualmente autenticado."
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Reemplazar perfil por completo (PUT)",
        description="Reemplaza todos los datos del perfil. Se deben enviar todos los campos, de lo contrario los no enviados quedarán con valores nulos o por defecto."
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary="Actualizar perfil parcialmente (PATCH)",
        description="Actualiza uno o más campos del perfil. Solo se necesita enviar los campos que se desean cambiar."
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


# ============================================================================
# VIEWS DE AUTENTICACIÓN
# ============================================================================

class RegistroInicialView(CreateAPIView):
    """
    Vista para el registro inicial (PASO 1)
    Solo email y password
    """
    queryset = User.objects.all()
    serializer_class = RegistroInicialSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Register Initial",
        description="Primer paso del registro: solo email y contraseña. "
                   "Después de esto, el usuario debe completar su perfil.",
        tags=['Autenticación'],
        responses={
            201: inline_serializer(
                name='RegistroExitosoResponse',
                fields={
                    'message': serializers.CharField(),
                    'usuario': UserSimpleSerializer(),
                    'siguiente_paso': serializers.CharField(),
                    'perfil_completo': serializers.BooleanField(),
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        """Crear usuario con datos iniciales"""
        return super().post(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Override para personalizar la respuesta"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        usuario = serializer.save()
        
        # Usar el serializer simple para la respuesta
        response_serializer = UserSimpleSerializer(usuario)
        
        return Response(
            {
                'message': 'Registro inicial exitoso. Ahora completa tu perfil.',
                'usuario': response_serializer.data,
                'perfil_completo': usuario.perfil_completo,
                'siguiente_paso': 'completar_perfil'
            },
            status=status.HTTP_201_CREATED
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vista personalizada para login con email, usando el serializer custom.
    """
    serializer_class = CustomTokenObtainPairSerializer

    @extend_schema(
        summary="Login de usuario",
        description="Autentica un usuario con email y contraseña, devuelve tokens JWT y estado del perfil",
        tags=['Autenticación'],
        responses={
            200: inline_serializer(
                name='LoginExitosoResponse',
                fields={
                    'access': serializers.CharField(),
                    'refresh': serializers.CharField(),
                    'message': serializers.CharField(),
                    'usuario': UserSerializer(),
                    'siguiente_paso': serializers.CharField(allow_null=True),
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class AdminLoginView(TokenObtainPairView):
    """
    Vista de login EXCLUSIVA para panel de administración.
    
    Solo permite acceso a usuarios con rol ADMIN o SUPERUSUARIO.
    Si un usuario con rol LECTOR intenta acceder, se deniega el login.
    """
    serializer_class = CustomTokenObtainPairSerializer

    @extend_schema(
        summary="Login para panel de administración",
        description="Login exclusivo para Admin y Superusuario. Los usuarios con rol LECTOR no pueden acceder.",
        tags=['Autenticación - Panel Admin'],
        responses={
            200: inline_serializer(
                name='AdminLoginExitosoResponse',
                fields={
                    'access': serializers.CharField(),
                    'refresh': serializers.CharField(),
                    'message': serializers.CharField(),
                    'usuario': UserSerializer(),
                    'can_access_panel': serializers.BooleanField(),
                }
            ),
            403: inline_serializer(
                name='AdminLoginForbiddenResponse',
                fields={
                    'error': serializers.CharField(),
                    'message': serializers.CharField(),
                    'role': serializers.CharField(),
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        # Primero autenticamos al usuario normalmente
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Obtener el usuario autenticado
            from rest_framework_simplejwt.tokens import AccessToken
            access_token = response.data.get('access')
            
            # Decodificar el token para obtener el user_id
            token = AccessToken(access_token)
            user_id = token['user_id']
            
            # Obtener el usuario de la base de datos
            try:
                user = User.objects.get(id=user_id)
                
                # Verificar si el usuario puede acceder al panel
                if not user.can_access_panel():
                    return Response({
                        'error': 'Acceso denegado',
                        'message': 'Solo usuarios con rol de Administrador o Superusuario pueden acceder al panel de control.',
                        'role': user.get_role_display(),
                        'redirect_to': '/'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                # Si puede acceder, agregar información adicional a la respuesta
                response.data['can_access_panel'] = True
                response.data['panel_access'] = {
                    'can_manage_content': user.can_manage_content(),
                    'can_assign_roles': user.can_assign_roles(),
                    'is_superuser': user.is_superusuario_role()
                }
                
            except User.DoesNotExist:
                return Response({
                    'error': 'Usuario no encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
        
        return response


class LogoutView(APIView):
    """
    Vista para cerrar sesión
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Logout de usuario",
        description="Cierra la sesión del usuario invalidando el refresh token",
        tags=['Autenticación']
    )
    def post(self, request):
        """Cerrar sesión del usuario"""
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            logout(request)
            return Response(
                {'message': 'Logout exitoso'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': 'Token inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )


# ============================================================================
# VIEWS DE RECUPERACIÓN DE CONTRASEÑA
# ============================================================================

@extend_schema(
    summary="Solicitar restablecimiento de contraseña",
    description="Envía un correo con un enlace para restablecer la contraseña",
    request=RequestPasswordResetSerializer,   # 👈 Aquí indicas el serializer
    responses={200: inline_serializer(
        name="PasswordResetResponse",
        fields={"message": serializers.CharField()}
    )},
    tags=['Autenticación']
)
class RequestPasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RequestPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "No existe un usuario con ese correo"}, status=404)

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = f"http://localhost:5173/reset-password-confirm/?uid={uid}&token={token}"

        # Crear mensaje de email sin caracteres Unicode problemáticos
        subject = "Recupera tu contraseña"
        message = f"""Hola {user.email},

Usa el siguiente enlace para restablecer tu contraseña:
{reset_link}

Este enlace expira en 1 hora.

Si no solicitaste este cambio, ignora este mensaje.

Saludos,
Equipo de Revista Meta Mining"""
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
            return Response({
                "message": "Hemos enviado un enlace de recuperación a tu correo electrónico",
                "email": user.email,
                "success": True
            }, status=200)
            
        except Exception as e:
            # En caso de error, devolver respuesta pero no exponer detalles del error
            return Response({
                "message": "Error al enviar el email. Por favor, intenta nuevamente más tarde.",
                "error": "EMAIL_SEND_FAILED",
                "success": False
            }, status=500)


class ResetPasswordConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Confirmar restablecimiento de contraseña",
        description="Confirma el restablecimiento de contraseña usando el token y el uid. Requiere que las contraseñas coincidan.",
        request=ResetPasswordConfirmSerializer,
        responses={
            200: inline_serializer(
                name="PasswordResetConfirmResponse",
                fields={"message": serializers.CharField()}
            ),
            400: inline_serializer(
                name="PasswordResetConfirmErrorResponse",
                fields={
                    "error": serializers.CharField(),
                    "details": serializers.DictField(required=False)
                }
            )
        },
        tags=['Autenticación']
    )
    def post(self, request):
        serializer = ResetPasswordConfirmSerializer(data=request.data)
        
        # Validar datos del serializer (incluye validación de contraseñas)
        if not serializer.is_valid():
            return Response({
                "error": "Datos de entrada inválidos",
                "details": serializer.errors
            }, status=400)

        uid = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        try:
            uid = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({
                "error": "Usuario inválido",
                "message": "El enlace de recuperación no es válido"
            }, status=400)

        if not default_token_generator.check_token(user, token):
            return Response({
                "error": "Token inválido o expirado",
                "message": "El enlace de recuperación ha expirado o no es válido"
            }, status=400)

        # Establecer nueva contraseña
        user.set_password(new_password)
        user.save()

        return Response({
            "message": "Contraseña restablecida exitosamente",
            "success": True
        }, status=200)


# ============================================================================
# VIEWS DE GESTIÓN DE ROLES (Solo Superusuario)
# ============================================================================

@extend_schema(
    summary="Asignar rol a usuario",
    description="Permite a un superusuario asignar roles (LECTOR, ADMIN) a otros usuarios. "
                "Solo los superusuarios pueden usar este endpoint.",
    tags=['Roles - Gestión'],
    request=inline_serializer(
        name='AssignRoleRequest',
        fields={
            'user_id': serializers.IntegerField(help_text="ID del usuario al que se asignará el rol"),
            'role': serializers.ChoiceField(
                choices=['LECTOR', 'ADMIN'],
                help_text="Rol a asignar: LECTOR o ADMIN"
            )
        }
    ),
    responses={
        200: inline_serializer(
            name='AssignRoleResponse',
            fields={
                'message': serializers.CharField(),
                'user': UserSerializer(),
                'previous_role': serializers.CharField(),
                'new_role': serializers.CharField()
            }
        ),
        403: inline_serializer(
            name='AssignRoleForbiddenResponse',
            fields={'error': serializers.CharField()}
        ),
        404: inline_serializer(
            name='AssignRoleNotFoundResponse',
            fields={'error': serializers.CharField()}
        )
    }
)
class AssignRoleView(APIView):
    """
    Vista para asignar roles a usuarios.
    
    Solo los SUPERUSUARIOS pueden asignar roles.
    Los superusuarios solo pueden asignar roles LECTOR o ADMIN (no pueden crear otros superusuarios).
    """
    permission_classes = [IsSuperusuario]
    
    def post(self, request):
        """Asignar un rol a un usuario"""
        user_id = request.data.get('user_id')
        new_role = request.data.get('role')
        
        # Validaciones
        if not user_id or not new_role:
            return Response(
                {'error': 'Se requiere user_id y role'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar que el rol sea válido
        valid_roles = ['LECTOR', 'ADMIN']
        if new_role not in valid_roles:
            return Response(
                {
                    'error': f'Rol inválido. Los roles permitidos son: {", ".join(valid_roles)}',
                    'note': 'Solo los superusuarios pueden crear otros superusuarios desde la terminal'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Buscar el usuario
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': f'No se encontró un usuario con ID {user_id}'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # No permitir cambiar el rol de un superusuario
        if user.role == 'SUPERUSUARIO':
            return Response(
                {
                    'error': 'No se puede modificar el rol de un superusuario',
                    'note': 'Los superusuarios solo pueden ser gestionados desde la terminal'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # No permitir que se cambie su propio rol
        if user.id == request.user.id:
            return Response(
                {'error': 'No puedes cambiar tu propio rol'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Guardar el rol anterior
        previous_role = user.role
        
        # Asignar el nuevo rol
        user.role = new_role
        user.save()
        
        # Serializar la respuesta
        serializer = UserSerializer(user)
        
        return Response({
            'message': f'Rol asignado exitosamente',
            'user': serializer.data,
            'previous_role': previous_role,
            'new_role': new_role,
            'assigned_by': request.user.email
        }, status=status.HTTP_200_OK)


@extend_schema(
    summary="Listar usuarios con sus roles",
    description="Obtiene una lista de todos los usuarios del sistema con sus roles. "
                "Solo accesible para superusuarios.",
    tags=['Roles - Gestión'],
    responses={
        200: UserSerializer(many=True)
    }
)
class ListUsersWithRolesView(generics.ListAPIView):
    """
    Vista para listar todos los usuarios con sus roles.
    Solo accesible para superusuarios.
    
    Funcionalidades:
    - 🔍 Búsqueda: ?search=término (busca en email, nombre, apellido)
      ✨ La búsqueda ignora acentos y diacríticos
      - Buscar "jose" encontrará "José" y "jose"
      - Buscar "maría" encontrará "maria" y "maría"
    - 📄 Paginación: 8 usuarios por página (configurable hasta 100)
    
    Parámetros:
    - ?search=término - Buscar usuarios
    - ?page=1 - Número de página
    - ?page_size=8 - Cantidad de usuarios por página (máx. 100)
    
    Ejemplos de uso:
    - GET /api/v1/users/roles/users/?search=jose (encuentra "José")
    - GET /api/v1/users/roles/users/?search=admin@example.com
    - GET /api/v1/users/roles/users/?page=2&page_size=20
    """
    queryset = User.objects.all().order_by('-fecha_creacion')
    serializer_class = UserSerializer
    permission_classes = [IsSuperusuario]
    pagination_class = UsersPagination
    
    # Configuración de búsqueda sin acentos
    filter_backends = [AccentInsensitiveSearchFilter]
    search_fields = ['email', 'first_name', 'last_name', 'usuario_unico']