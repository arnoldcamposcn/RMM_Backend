from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Blog, ComentarioBlog, LikeBlog, Categoria_Blog
from app.articles.serializers import ArticuloSerializer

User = get_user_model()


class CategoriaBlogSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar información de la categoría del blog.
    """
    class Meta:
        model = Categoria_Blog
        fields = ["id", "nombre_categoria", "slug"]


class AutorBlogSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar información completa del autor en blogs.
    Incluye email y username para una mejor experiencia de usuario.
    """
    class Meta:
        model = User
        fields = ["id", "email", "usuario_unico"]


class OptionalParentFieldBlog(serializers.PrimaryKeyRelatedField):
    """
    Campo personalizado para manejar el parent de comentarios de blog.
    Convierte strings vacíos y valores falsy a None automáticamente.
    """
    def to_internal_value(self, data):
        # Si el valor está vacío, es None, 0, o string vacío -> convertir a None
        if not data or data == "" or data == "0" or data == 0:
            return None
        return super().to_internal_value(data)


class LikeBlogSerializer(serializers.ModelSerializer):
    """
    Serializer para likes de blogs.
    Solo 'me gusta' - sin 'no me gusta'.
    """
    usuario = AutorBlogSerializer(read_only=True)  # Incluir información detallada del usuario
    
    class Meta:
        model = LikeBlog
        fields = ["id", "usuario", "creado_en"]
        read_only_fields = ["usuario", "creado_en"]


class ComentarioBlogSerializer(serializers.ModelSerializer):
    
    autor = AutorBlogSerializer(read_only=True)
    respuestas = serializers.SerializerMethodField()
    parent = OptionalParentFieldBlog(
        queryset=ComentarioBlog.objects.all(),
        required=False,
        allow_null=True,
        default="",
        help_text="ID del comentario padre. Dejar vacío (\"\") para comentario independiente, o número para responder."
    )

    # Nuevo campo de nivel
    nivel = serializers.IntegerField(read_only=True)

    class Meta:
        model = ComentarioBlog
        fields = [
            "id", "blog", "autor", "contenido", "parent", "nivel", "creado_en", "respuestas"
        ]
        read_only_fields = ["autor", "nivel", "creado_en", "respuestas"]

    def validate_parent(self, value):
        if value and value.nivel >= ComentarioBlog.MAX_DEPTH:
            raise serializers.ValidationError(f"No se puede responder a un comentario de nivel {ComentarioBlog.MAX_DEPTH}.")
        return value

    def get_respuestas(self, obj):
        # Se optimiza para evitar N+1 queries usando prefetch_related en view
        return ComentarioBlogSerializer(
            obj.respuestas.all().order_by("-creado_en"),
            many=True,
            context=self.context
        ).data

    def create(self, validated_data):
        validated_data["autor"] = self.context["request"].user
        return super().create(validated_data)


class BlogSerializer(serializers.ModelSerializer):
    categoria_blog = CategoriaBlogSerializer(read_only=True)
    comentarios = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    articulos = ArticuloSerializer(many=True, read_only=True)

    class Meta:
        model = Blog
        fields = [
            "id", "titulo_blog", "contenido", "imagen_principal", "banner", "fecha_publicacion",
            "categoria_blog", "comentarios", "likes_count", "articulos"
        ]

    def get_comentarios(self, obj):
        comentarios_principales = obj.comentarios.filter(parent__isnull=True)
        return ComentarioBlogSerializer(
            comentarios_principales,
            many=True,
            context=self.context
        ).data

    def get_likes_count(self, obj):
        return obj.likes.count()

