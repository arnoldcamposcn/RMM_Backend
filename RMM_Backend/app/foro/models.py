from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.exceptions import ValidationError

User = settings.AUTH_USER_MODEL


class Tema(models.Model):
    """
    Modelo para los temas (foros) creados por los usuarios.
    """
    titulo = models.CharField("Título del tema", max_length=255)
    contenido = models.TextField("Contenido del tema")
    autor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="temas_foro"
    )
    categoria_foro = models.ForeignKey(
        "Categoria_Foro",
        on_delete=models.CASCADE,
        related_name="temas",
        verbose_name="Categoría del foro",
        help_text="Selecciona la categoría a la que pertenece este tema",
        null=True,
        blank=True
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creado_en"]
        verbose_name = "Tema de Foro"
        verbose_name_plural = "Temas de Foro"

    def __str__(self):
        return self.titulo

class Categoria_Foro(models.Model):
    nombre_categoria = models.CharField("Nombre de la categoría", max_length=200, unique=True)
    slug = models.SlugField("Slug", unique=True, blank=True, editable=False)

    class Meta:
        verbose_name = "Categoría de Foro"
        verbose_name_plural = "Categorías"
        ordering = ["nombre_categoria"]

    def __str__(self):
        return self.nombre_categoria

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre_categoria)
        super().save(*args, **kwargs)



class ComentarioTema(models.Model):
    MAX_DEPTH = 5  # Límite de profundidad
    """
    Comentarios hechos en un tema del foro.
    """
    tema = models.ForeignKey(
        Tema, on_delete=models.CASCADE, related_name="comentarios"
    )
    autor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comentarios_foro"
    )
    contenido = models.TextField("Contenido del comentario")
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="respuestas"
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    # Nuevo campo para controlar la profundidad
    nivel = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        ordering = ["-creado_en"]
        indexes = [
            models.Index(fields=["tema", "parent"]),
            models.Index(fields=["tema", "nivel"]),
        ]

    def clean(self):
        # Verificar que no exceda el nivel máximo
        if self.parent:
            self.nivel = self.parent.nivel + 1
        if self.nivel > self.MAX_DEPTH:
            raise ValidationError(f"No se permite crear comentarios más profundos de {self.MAX_DEPTH} niveles.")

    def save(self, *args, **kwargs):
        self.clean()  # Validar y establecer nivel
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Comentario de {self.autor} en {self.tema}"


class LikeTema(models.Model):
    """
    Sistema de likes para temas del foro.
    Un usuario puede dar 'me gusta' a un tema. Si no le gusta, simplemente no da like.
    """
    tema = models.ForeignKey(
        Tema, on_delete=models.CASCADE, related_name="likes"
    )
    usuario = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="likes_temas"
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("tema", "usuario")
        verbose_name = "Like de Tema"
        verbose_name_plural = "Likes de Temas"

    def __str__(self):
        return f"{self.usuario} 👍 {self.tema.titulo}"


class LikeComentarioTema(models.Model):
    """
    Sistema de likes para comentarios individuales del foro.
    Un usuario puede dar 'me gusta' a un comentario específico.
    """
    comentario = models.ForeignKey(
        ComentarioTema, on_delete=models.CASCADE, related_name="likes"
    )
    usuario = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="likes_comentarios_foro"
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("comentario", "usuario")
        verbose_name = "Like de Comentario de Foro"
        verbose_name_plural = "Likes de Comentarios de Foro"

    def __str__(self):
        return f"{self.usuario} 👍 comentario en {self.comentario.tema.titulo}"
