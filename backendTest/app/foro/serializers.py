from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Tema, ComentarioTema, LikeTema

User = get_user_model()


class AutorForoSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar información completa del autor en el foro.
    Incluye email y username para una mejor experiencia de usuario.
    """
    class Meta:
        model = User
        fields = ["id", "email", "usuario_unico"]


class OptionalParentFieldTema(serializers.PrimaryKeyRelatedField):
    """
    Campo personalizado para manejar el parent de comentarios de temas.
    Convierte strings vacíos y valores falsy a None automáticamente.
    """
    def to_internal_value(self, data):
        # Si el valor está vacío, es None, 0, o string vacío -> convertir a None
        if not data or data == "" or data == "0" or data == 0:
            return None
        return super().to_internal_value(data)


class LikeTemaSerializer(serializers.ModelSerializer):
    """
    Serializer para likes de temas del foro.
    Solo 'me gusta' - sin 'no me gusta'.
    """
    class Meta:
        model = LikeTema
        fields = ["id", "usuario", "creado_en"]
        read_only_fields = ["usuario", "creado_en"]


class ComentarioTemaSerializer(serializers.ModelSerializer):
    """
    Serializer para comentarios de temas del foro.
    Los comentarios ya no tienen sistema de likes individual.
    
    Para crear comentarios:
    - Comentario independiente: parent = "" (string vacío) o no incluir el campo
    - Respuesta a comentario: parent = ID del comentario padre (ejemplo: parent = 5)
    """
    autor = AutorForoSerializer(read_only=True)
    respuestas = serializers.SerializerMethodField()
    parent = OptionalParentFieldTema(
        queryset=ComentarioTema.objects.all(),
        required=False,
        allow_null=True,
        default="",
        help_text="ID del comentario padre. Dejar vacío (\"\") para comentario independiente, o número para responder."
    )

    class Meta:
        model = ComentarioTema
        fields = [
            "id", "tema", "autor", "contenido", "parent",
            "creado_en", "respuestas"
        ]
        read_only_fields = ["autor", "creado_en", "respuestas"]

    def get_respuestas(self, obj):
        """Traer respuestas en forma anidada"""
        return ComentarioTemaSerializer(
            obj.respuestas.all(), 
            many=True, 
            context=self.context
        ).data


class TemaSerializer(serializers.ModelSerializer):
    """
    Serializer para temas del foro con sistema de likes.
    """
    autor = AutorForoSerializer(read_only=True)
    comentarios = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()

    class Meta:
        model = Tema
        fields = [
            "id", "titulo", "contenido", "autor", "creado_en", "actualizado_en",
            "comentarios", "likes_count"
        ]
        read_only_fields = ["autor", "creado_en", "actualizado_en"]

    def get_comentarios(self, obj):
        """Solo comentarios principales (sin parent), con sus respuestas anidadas"""
        comentarios_principales = obj.comentarios.filter(parent__isnull=True)
        return ComentarioTemaSerializer(
            comentarios_principales, 
            many=True, 
            context=self.context
        ).data

    def get_likes_count(self, obj):
        """Cantidad total de 'me gusta'"""
        return obj.likes.count()
