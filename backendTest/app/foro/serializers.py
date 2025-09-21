from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Tema, ComentarioTema, LikeTema, Categoria_Foro

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


class ComentarioTemaSerializer(serializers.ModelSerializer):
    autor = AutorForoSerializer(read_only=True)
    respuestas = serializers.SerializerMethodField()
    parent = OptionalParentFieldTema(
        queryset=ComentarioTema.objects.all(),
        required=False,
        allow_null=True,
        default="",
        help_text="ID del comentario padre. Dejar vacío para comentario independiente."
    )

    class Meta:
        model = ComentarioTema
        fields = [
            "id", "tema", "autor", "contenido", "parent",
            "creado_en", "respuestas"
        ]
        read_only_fields = ["autor", "creado_en", "respuestas"]

    def get_respuestas(self, obj):
        return ComentarioTemaSerializer(
            obj.respuestas.all(),
            many=True,
            context=self.context
        ).data


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
            "id", "titulo", "contenido", "autor",
            "categoria_foro", "categoria_foro_id",
            "creado_en", "actualizado_en",
            "comentarios", "likes_count"
        ]
        read_only_fields = ["autor", "creado_en", "actualizado_en"]

    def get_comentarios(self, obj):
        comentarios_principales = obj.comentarios.filter(parent__isnull=True)
        return ComentarioTemaSerializer(
            comentarios_principales,
            many=True,
            context=self.context
        ).data

    def get_likes_count(self, obj):
        return obj.likes.count()
