from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Articulos, ComentarioArticulo, LikeArticulo
from app.blog.models import Categoria_Blog

User = get_user_model()


class AutorArticuloSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar información completa del autor en artículos.
    Incluye email y username para una mejor experiencia de usuario.
    """
    class Meta:
        model = User
        fields = ["id", "email", "usuario_unico"]


class CategoriaArticuloSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar categorías de artículos.
    Reutiliza el modelo Categoria_Blog para mantener consistencia.
    """
    class Meta:
        model = Categoria_Blog
        fields = ["id", "nombre_categoria", "slug"]


class OptionalParentField(serializers.PrimaryKeyRelatedField):
    """
    Campo personalizado para manejar el parent de comentarios.
    Convierte strings vacíos y valores falsy a None automáticamente.
    """
    def to_internal_value(self, data):
        # Si el valor está vacío, es None, 0, o string vacío -> convertir a None
        if not data or data == "" or data == "0" or data == 0:
            return None
        return super().to_internal_value(data)


class LikeArticuloSerializer(serializers.ModelSerializer):
    """
    Serializer para likes de artículos.
    Solo 'me gusta' - sin 'no me gusta'.
    """
    usuario = AutorArticuloSerializer(read_only=True)  # Incluir información detallada del usuario
    
    class Meta:
        model = LikeArticulo
        fields = ["id", "usuario", "creado_en"]
        read_only_fields = ["usuario", "creado_en"]


class ComentarioArticuloSerializer(serializers.ModelSerializer):
    """
    Serializer para comentarios de artículos.
    Los comentarios ya no tienen sistema de likes individual.
    
    Para crear comentarios:
    - Comentario independiente: parent = "" (string vacío) o no incluir el campo
    - Respuesta a comentario: parent = ID del comentario padre (ejemplo: parent = 5)
    """
    autor = AutorArticuloSerializer(read_only=True)
    respuestas = serializers.SerializerMethodField()
    parent = OptionalParentField(
        queryset=ComentarioArticulo.objects.all(),
        required=False,
        allow_null=True,
        default="",
        help_text="ID del comentario padre. Dejar vacío (\"\") para comentario independiente, o número para responder."
    )

    class Meta:
        model = ComentarioArticulo
        fields = [
            "id", "articulo", "autor", "contenido", "parent",
            "creado_en", "respuestas"
        ]
        read_only_fields = ["autor", "creado_en", "respuestas"]

    def get_respuestas(self, obj):
        """Traer respuestas en forma anidada"""
        return ComentarioArticuloSerializer(
            obj.respuestas.all(), 
            many=True, 
            context=self.context
        ).data


class ArticuloSerializer(serializers.ModelSerializer):
    """
    Serializer para artículos con sistema de likes y categorías.
    """
    comentarios = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    categoria_articulo = CategoriaArticuloSerializer(read_only=True)
    categoria_articulo_id = serializers.PrimaryKeyRelatedField(
        queryset=Categoria_Blog.objects.all(),
        source="categoria_articulo",
        write_only=True,
        required=False,
        allow_null=True,
        help_text="ID de la categoría del artículo (opcional)"
    )

    class Meta:
        model = Articulos
        fields = [
            "id", "titulo_articulo", "contenido", "imagen_principal", "banner", "fecha_publicacion",
            "categoria_articulo", "categoria_articulo_id", "comentarios", "likes_count"
        ]

    def get_comentarios(self, obj):
        """Solo comentarios principales (sin parent), con sus respuestas anidadas"""
        comentarios_principales = obj.comentarios.filter(parent__isnull=True)
        return ComentarioArticuloSerializer(
            comentarios_principales, 
            many=True, 
            context=self.context
        ).data

    def get_likes_count(self, obj):
        """Cantidad total de 'me gusta'"""
        return obj.likes.count()
