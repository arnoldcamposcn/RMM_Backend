from rest_framework import generics, permissions, serializers
from django.contrib.auth import logout
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_spectacular.utils import extend_schema, inline_serializer
from .serializers import RegistroInicialSerializer, UserSimpleSerializer, UserSerializer, CustomTokenObtainPairSerializer
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

