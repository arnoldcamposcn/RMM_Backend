from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Blog, ComentarioBlog, LikeBlog, Categoria_Blog

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
    class Meta:
        model = LikeBlog
        fields = ["id", "usuario", "creado_en"]
        read_only_fields = ["usuario", "creado_en"]


class ComentarioBlogSerializer(serializers.ModelSerializer):
    """
    Serializer para comentarios de blogs.
    Los comentarios ya no tienen sistema de likes individual.
    
    Para crear comentarios:
    - Comentario independiente: parent = "" (string vacío) o no incluir el campo
    - Respuesta a comentario: parent = ID del comentario padre (ejemplo: parent = 5)
    """
    autor = AutorBlogSerializer(read_only=True)
    respuestas = serializers.SerializerMethodField()
    parent = OptionalParentFieldBlog(
        queryset=ComentarioBlog.objects.all(),
        required=False,
        allow_null=True,
        default="",
        help_text="ID del comentario padre. Dejar vacío (\"\") para comentario independiente, o número para responder."
    )

    class Meta:
        model = ComentarioBlog
        fields = [
            "id", "blog", "autor", "contenido", "parent",
            "creado_en", "respuestas"
        ]
        read_only_fields = ["autor", "creado_en", "respuestas"]

    def get_respuestas(self, obj):
        """Traer respuestas en forma anidada"""
        return ComentarioBlogSerializer(
            obj.respuestas.all(), 
            many=True, 
            context=self.context
        ).data


class BlogSerializer(serializers.ModelSerializer):
    """
    Serializer para blogs con sistema de likes.
    """
    categoria_blog = CategoriaBlogSerializer(read_only=True)
    comentarios = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()

    class Meta:
        model = Blog
        fields = [
            "id", "titulo_blog", "contenido", "imagen_principal", "banner", "fecha_publicacion",
            "categoria_blog", "comentarios", "likes_count"
        ]

    def get_comentarios(self, obj):
        """Solo comentarios principales (sin parent), con sus respuestas anidadas"""
        comentarios_principales = obj.comentarios.filter(parent__isnull=True)
        return ComentarioBlogSerializer(
            comentarios_principales, 
            many=True, 
            context=self.context
        ).data

    def get_likes_count(self, obj):
        """Cantidad total de 'me gusta'"""
        return obj.likes.count()
