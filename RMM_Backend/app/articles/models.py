from django.db import models
from django.conf import settings
from ckeditor.fields import RichTextField
from django.core.exceptions import ValidationError

User = settings.AUTH_USER_MODEL

class Articulos(models.Model):
    titulo_articulo = models.CharField("Título del artículo", max_length=200)
    contenido = RichTextField("Contenido", blank=True)
    imagen_principal = models.ImageField("Imagen", upload_to="RMM/Articulos-ImagenPrincipal/", null=True, blank=True)
    banner = models.ImageField("Banner", upload_to="RMM/Articulos-Banner/", null=True, blank=True)
    fecha_publicacion = models.DateField("Fecha de publicación" , null=True, blank=True)

    class Meta:
        ordering = ["-fecha_publicacion"]
        verbose_name = "Artículo"
        verbose_name_plural = "Artículos"

    def __str__(self):
        return self.titulo_articulo


class ComentarioArticulo(models.Model):
    MAX_DEPTH = 5  # Límite de profundidad
    articulo = models.ForeignKey(
        Articulos, on_delete=models.CASCADE, related_name="comentarios"
    )
    autor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comentarios_articulos"
    )
    contenido = models.TextField("Contenido del comentario")
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="respuestas"
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    nivel = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        ordering = ["-creado_en"]
        indexes = [
            models.Index(fields=["articulo", "parent"]),
            models.Index(fields=["articulo", "nivel"]),
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
        return f"Comentario de {self.autor} en {self.articulo}"


class LikeArticulo(models.Model):
    """
    Sistema de likes para artículos.
    Un usuario puede dar 'me gusta' a un artículo. Si no le gusta, simplemente no da like.
    """
    articulo = models.ForeignKey(
        Articulos, on_delete=models.CASCADE, related_name="likes"
    )
    usuario = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="likes_articulos"
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("articulo", "usuario")
        verbose_name = "Like de Artículo"
        verbose_name_plural = "Likes de Artículos"

    def __str__(self):
        return f"{self.usuario} 👍 {self.articulo.titulo_articulo}"
