from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Blog, ComentarioBlog, LikeBlog
from app.articles.serializers import ArticuloSerializer

User = get_user_model()


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
    comentarios = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    articulos = ArticuloSerializer(many=True, read_only=True)
    articulos_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="Lista de IDs de artículos a asociar con este blog"
    )

    class Meta:
        model = Blog
        fields = [
            "id", "titulo_blog", "contenido", "imagen_principal", "banner", "fecha_publicacion",
            "comentarios", "likes_count", "articulos", "articulos_ids"
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

    def create(self, validated_data):
        # Extraer los IDs de artículos
        articulos_ids = validated_data.pop('articulos_ids', [])
        
        # Convertir string a lista si es necesario (para FormData)
        if isinstance(articulos_ids, str):
            if articulos_ids:
                articulos_ids = [int(id.strip()) for id in articulos_ids.split(',') if id.strip()]
            else:
                articulos_ids = []
        
        # Crear el blog
        blog = Blog.objects.create(**validated_data)
        
        # Asociar los artículos si se proporcionaron IDs
        if articulos_ids:
            from app.articles.models import Articulos
            articulos = Articulos.objects.filter(id__in=articulos_ids)
            blog.articulos.set(articulos)
        
        return blog

    def update(self, instance, validated_data):
        # Extraer los IDs de artículos
        articulos_ids = validated_data.pop('articulos_ids', None)
        
        # Convertir string a lista si es necesario (para FormData)
        if isinstance(articulos_ids, str):
            if articulos_ids:
                articulos_ids = [int(id.strip()) for id in articulos_ids.split(',') if id.strip()]
            else:
                articulos_ids = []
        
        # Actualizar los campos del blog
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Actualizar los artículos si se proporcionaron IDs
        if articulos_ids is not None:
            from app.articles.models import Articulos
            articulos = Articulos.objects.filter(id__in=articulos_ids)
            instance.articulos.set(articulos)
        
        return instance

