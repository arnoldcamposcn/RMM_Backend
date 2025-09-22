from django.db import models
from django.conf import settings
from ckeditor.fields import RichTextField


User = settings.AUTH_USER_MODEL


class Articulos(models.Model):
    titulo_articulo = models.CharField("Título del artículo", max_length=200)
    contenido = RichTextField("Contenido", blank=True)
    imagen_principal = models.ImageField("Imagen", upload_to="articulos/", null=True, blank=True)
    banner = models.ImageField("Banner", upload_to="banners/", null=True, blank=True)
    fecha_publicacion = models.DateField("Fecha de publicación")
    categoria_articulo = models.ForeignKey(
        'blog.Categoria_Blog',
        on_delete=models.CASCADE,
        related_name="articulos",
        verbose_name="Categoría del artículo",
        help_text="Selecciona la categoría a la que pertenece este artículo",
        null=True,
        blank=True
    )

    class Meta:
        ordering = ["-fecha_publicacion"]
        verbose_name = "Artículo"
        verbose_name_plural = "Artículos"

    def __str__(self):
        return self.titulo_articulo


class ComentarioArticulo(models.Model):
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

    class Meta:
        ordering = ["-creado_en"]

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
