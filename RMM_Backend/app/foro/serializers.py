from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Tema, ComentarioTema, LikeTema, LikeComentarioTema, Categoria_Foro

User = get_user_model()


class AutorForoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "usuario_unico"]


class CategoriaForoSerializer(serializers.ModelSerializer):
    """Serializer para mostrar categorías de foros"""
    class Meta:
        model = Categoria_Foro
        fields = ["id", "nombre_categoria", "slug"]


class OptionalParentFieldTema(serializers.PrimaryKeyRelatedField):
    def to_internal_value(self, data):
        if not data or data == "" or data == "0" or data == 0:
            return None
        return super().to_internal_value(data)


class LikeTemaSerializer(serializers.ModelSerializer):
    """
    Serializer para likes de temas del foro.
    Solo 'me gusta' - sin 'no me gusta'.
    """
    usuario = AutorForoSerializer(read_only=True)  # Incluir información detallada del usuario
    
    class Meta:
        model = LikeTema
        fields = ["id", "usuario", "creado_en"]
        read_only_fields = ["usuario", "creado_en"]


class LikeComentarioTemaSerializer(serializers.ModelSerializer):
    """
    Serializer para likes de comentarios individuales del foro.
    Solo 'me gusta' - sin 'no me gusta'.
    """
    usuario = AutorForoSerializer(read_only=True)  # Incluir información detallada del usuario
    
    class Meta:
        model = LikeComentarioTema
        fields = ["id", "usuario", "creado_en"]
        read_only_fields = ["usuario", "creado_en"]


class ComentarioTemaSerializer(serializers.ModelSerializer):
    autor = AutorForoSerializer(read_only=True)
    respuestas = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    parent = OptionalParentFieldTema(
        queryset=ComentarioTema.objects.all(),
        required=False,
        allow_null=True,
        default="",
        help_text="ID del comentario padre. Dejar vacío para comentario independiente."
    )
    
    # Nuevo campo para el nivel de anidación
    nivel = serializers.IntegerField(read_only=True)

    class Meta:
        model = ComentarioTema
        fields = [
            "id", "tema", "autor", "contenido", "parent", "nivel",
            "creado_en", "respuestas", "likes_count"
        ]
        read_only_fields = ["autor", "nivel", "creado_en", "respuestas", "likes_count"]

    def validate_parent(self, value):
        if value and value.nivel >= ComentarioTema.MAX_DEPTH:
            raise serializers.ValidationError(f"No se puede responder a un comentario de nivel {ComentarioTema.MAX_DEPTH}.")
        return value

    def get_respuestas(self, obj):
        return ComentarioTemaSerializer(
            obj.respuestas.all().order_by("-creado_en"),
            many=True,
            context=self.context
        ).data
    
    def get_likes_count(self, obj):
        """Cantidad total de 'me gusta' en este comentario"""
        return obj.likes.count()
    
    def create(self, validated_data):
        validated_data["autor"] = self.context["request"].user
        return super().create(validated_data)


class TemaSerializer(serializers.ModelSerializer):
    autor = AutorForoSerializer(read_only=True)
    comentarios = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()

    # Mostrar categoría completa en GET
    categoria_foro = CategoriaForoSerializer(read_only=True)
    # Permitir asignar categoría por ID en POST/PUT
    categoria_foro_id = serializers.PrimaryKeyRelatedField(
        queryset=Categoria_Foro.objects.all(),
        source="categoria_foro",
        write_only=True
    )

    class Meta:
        model = Tema
        fields = [
            "id", "titulo", "contenido", "imagen", "autor",
            "categoria_foro", "categoria_foro_id",
            "creado_en", "actualizado_en",
            "comentarios", "likes_count"
        ]
        read_only_fields = ["autor", "creado_en", "actualizado_en"]

    def validate_imagen(self, value):
        """Validar imagen - permitir string vacío o URL válida"""
        if not value or value.strip() == "" or value == "null":
            return None
        # Si hay valor, puede ser una URL o path de imagen
        return value.strip()

    def get_comentarios(self, obj):
        comentarios_principales = obj.comentarios.filter(parent__isnull=True)
        return ComentarioTemaSerializer(
            comentarios_principales,
            many=True,
            context=self.context
        ).data

    def get_likes_count(self, obj):
        return obj.likes.count()
