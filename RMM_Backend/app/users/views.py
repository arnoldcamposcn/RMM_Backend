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