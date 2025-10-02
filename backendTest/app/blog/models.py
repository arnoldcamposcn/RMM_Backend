from django.db import models
from django.conf import settings
from ckeditor.fields import RichTextField
from django.utils.text import slugify
from app.articles.models import Articulos

User = settings.AUTH_USER_MODEL


class Blog(models.Model):
    titulo_blog = models.CharField("Título del noticia", max_length=200)
    contenido = RichTextField("Contenido", blank=True)
    imagen_principal = models.ImageField("Imagen", upload_to="blogs/", null=True, blank=True)
    banner = models.ImageField("Banner", upload_to="banners/", null=True, blank=True)
    fecha_publicacion = models.DateField("Fecha de publicación" , null=True, blank=True)
    categoria_blog = models.ForeignKey(
        'Categoria_Blog',
        on_delete=models.CASCADE,
        related_name="blogs",
        verbose_name="Categoría",
        help_text="Selecciona la categoría a la que pertenece este blog",
        null=True,
        blank=True,
    )
    # articulos = models.ManyToManyField(Articulos, blank=True, related_name="blogs")  # 👈 Relación ManyToMany
    articulos = models.ManyToManyField("articles.Articulos", blank=True, related_name="blogs")


    class Meta:
        ordering = ["-fecha_publicacion"]
        verbose_name = "Noticia"
        verbose_name_plural = "Noticias"

    def __str__(self):
        return self.titulo_blog


class Categoria_Blog(models.Model):
    nombre_categoria = models.CharField("Nombre de la noticias", max_length=200, unique=True)
    slug = models.SlugField("Slug", unique=True, blank=True, editable=False)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["nombre_categoria"]

    def __str__(self):
        return self.nombre_categoria

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre_categoria)
        super().save(*args, **kwargs)



class ComentarioBlog(models.Model):
    MAX_DEPTH = 5  # Límite de profundidad

    blog = models.ForeignKey(
        Blog, on_delete=models.CASCADE, related_name="comentarios"
    )
    autor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comentarios_blogs"
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
            models.Index(fields=["blog", "parent"]),
            models.Index(fields=["blog", "nivel"]),
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
        return f"Comentario de {self.autor} en {self.blog}"


class LikeBlog(models.Model):
    """
    Sistema de likes para blogs.
    Un usuario puede dar 'me gusta' a un blog. Si no le gusta, simplemente no da like.
    """
    blog = models.ForeignKey(
        Blog, on_delete=models.CASCADE, related_name="likes"
    )
    usuario = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="likes_blogs"
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("blog", "usuario")
        verbose_name = "Like de Blog"
        verbose_name_plural = "Likes de Blogs"

    def __str__(self):
        return f"{self.usuario} 👍 {self.blog.titulo_blog}"