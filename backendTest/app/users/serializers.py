from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()

# ============================================================================
# SERIALIZER PARA EL REGISTRO
# ============================================================================
class RegistroInicialSerializer(serializers.ModelSerializer):
    """
    Serializer para el primer paso del registro.
    Valida email y contraseñas.
    """
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text="La contraseña debe tener al menos 8 caracteres.",
    )

    confirm_password = serializers.CharField(
        write_only=True,
        help_text="Debe coincidir con la contraseña.",
    )

    class Meta:
        model = User
        fields = ['email', 'password', 'confirm_password']
        extra_kwargs = {
            'email': {
                'required': True,
                'help_text': 'Email válido para la cuenta'
            }
        }

    def validate_email(self, value):
        """Validar que el email sea único"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este email ya está registrado.")
        return value.lower()
    
    def validate(self, attrs):
        """Validaciones generales"""
        # Validar que las contraseñas coincidan
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError({
                'confirm_password': 'Las contraseñas no coinciden.'
            })

        # Validar fortaleza de la contraseña
        password = attrs.get('password')
        if password:
            try:
                validate_password(password)
            except ValidationError as e:
                raise serializers.ValidationError({'password': e.messages})

        # Remover confirm_password
        attrs.pop('confirm_password', None)
        return attrs

    def create(self, validated_data):
        """Crear usuario con registro inicial"""
        password = validated_data.pop('password')
        
        # Crear username temporal basado en email
        email = validated_data['email']
        base_username = email.split('@')[0].lower()
        
        # Asegurar que el usuario_unico sea único
        counter = 1
        usuario_unico = base_username
        while User.objects.filter(usuario_unico=usuario_unico).exists():
            usuario_unico = f"{base_username}{counter}"
            counter += 1
        
        usuario = User(
            usuario_unico=usuario_unico,
            perfil_completo=False,  # Importante: perfil no está completo
            **validated_data
        )
        usuario.set_password(password)
        usuario.save()
        return usuario

# ============================================================================
# SERIALIZER PARA EL LOGIN (JWT)
# ============================================================================
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer personalizado para login con email
    """

    def validate(self, attrs):
        """Añadir datos extra a la respuesta del token"""
        # (La validación de credenciales la hace TokenObtainPairSerializer)
        data = super().validate(attrs)

        # Añadir datos del usuario al response
        data['usuario'] = UserSerializer(self.user).data
        data['message'] = 'Login exitoso'
        
        # Determinar el siguiente paso (ej: completar perfil)
        siguiente_paso = None
        if not self.user.perfil_completo:
            siguiente_paso = 'completar_perfil'
        
        data['siguiente_paso'] = siguiente_paso
        
        return data

# ============================================================================
# SERIALIZER PARA EL PERFIL COMPLETO DEL USUARIO
# ============================================================================
class UserSerializer(serializers.ModelSerializer):
    """
    Serializer para ver y actualizar el perfil completo del usuario.
    """

    usuario_unico_sugerido = serializers.SerializerMethodField(read_only=True)

    def get_usuario_unico_sugerido(self, obj):
        """Devuelve el campo usuario_unico."""
        return obj.usuario_unico

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 
            'fecha_nacimiento', 'edad', 'pais', 'ciudad', 'genero',
            'perfil_url', 'biografia', 'facebook_url', 'linkedin_url',
            'telefono', 'usuario_unico', 'perfil_completo', 'fecha_creacion', 'fecha_actualizacion',
            'usuario_unico_sugerido'
        ]
        extra_kwargs = {
            'first_name':{
                'required': True,
                'help_text': 'Nombre del usuario (obligatorio)'
            },
            'last_name':{
                'required': True,
                'help_text': 'Apellido del usuario (obligatorio)'
            },
            'fecha_nacimiento':{
                'required': True,
                'help_text': 'Fecha de nacimiento del usuario (obligatorio)'
            },
            'pais':{
                'required': True,
                'help_text': 'País de residencia (obligatorio)'
            },
            'ciudad':{
                'help_text': 'Ciudad del usuario (opcional)'
            },
            'perfil_url':{
                'required': False,
                'allow_null': True,
                'help_text': 'URL del perfil (opcional)'
            },
            'facebook_url':{
                'required': False,
                'allow_null': True,
                'allow_blank': True,
                'help_text': 'URL de Facebook (opcional)'
            },
            'linkedin_url':{
                'required': False,
                'allow_null': True,
                'allow_blank': True,
                'help_text': 'URL de LinkedIn (opcional)'
            },
            'usuario_unico':{
                'help_text': 'Nombre de usuario único (opcional, se genera automáticamente)'
            }
        }
        read_only_fields = ['email', 'edad', 'fecha_creacion', 'fecha_actualizacion', 'perfil_completo']

    def update(self, instance, validated_data):
        """
        Actualiza el perfil y marca perfil_completo como True.
        """
        instance = super().update(instance, validated_data)
        
        # Marcar el perfil como completo después de la primera actualización
        if not instance.perfil_completo:
            instance.perfil_completo = True
            instance.save(update_fields=['perfil_completo'])
            
        return instance

# ============================================================================
# SERIALIZER SIMPLIFICADO DEL USUARIO
# ============================================================================
class UserSimpleSerializer(serializers.ModelSerializer):
    """
    Serializer ligero para respuestas rápidas.
    """
    class Meta:
        model = User
        fields = ['id', 'email', 'usuario_unico', 'perfil_completo']



# ======================================================================
# SERIALIZERS DE RECUPERACIÓN DE CONTRASEÑA
# ======================================================================

class RequestPasswordResetSerializer(serializers.Serializer):
    """
    Valida que el email se envíe correctamente
    """
    email = serializers.EmailField()

    
class ResetPasswordConfirmSerializer(serializers.Serializer):
    """
    Valida los datos que llegan para restablecer contraseña
    """
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(min_length=8, write_only=True)

    def validate(self, attrs):
        """Validar que las contraseñas coincidan"""
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')
        
        if new_password != confirm_password:
            raise serializers.ValidationError({
                'confirm_password': 'Las contraseñas no coinciden.'
            })
        
        # Validar fortaleza de la contraseña
        if new_password:
            try:
                validate_password(new_password)
            except ValidationError as e:
                raise serializers.ValidationError({'new_password': e.messages})
        
        return attrs
