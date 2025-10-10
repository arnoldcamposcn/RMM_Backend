from django.db import models
from ckeditor.fields import RichTextField 

#  Modelo para ediciones mensuales
class Ediciones(models.Model):
    numero_edicion = models.PositiveIntegerField("Número de edición", unique=True)
    titulo_edicion = models.CharField("Título de la edición", max_length=200)
    contenido = models.CharField("Descripción corta", max_length=5000, blank=True)
    imagen = models.ImageField("Imagen", upload_to="RMM/Ediciones/")
    fecha_publicacion = models.DateField("Fecha de publicación")
    url_impresa = models.URLField("Versión impresa (URL)", blank=True, null=True)

    class Meta:
        verbose_name = "Edición"
        verbose_name_plural = "Ediciones"
        ordering = ["-fecha_publicacion", "-numero_edicion"]

    def __str__(self):
        return f"Edición {self.numero_edicion} - {self.titulo_edicion}"



class Newsletter(models.Model):
    correo_electronico = models.EmailField("correo electrónico", max_length=200)
    fecha_publicacion = models.DateField("Fecha de envío")

    class Meta:
        ordering = ["-fecha_publicacion"]
        verbose_name = "Newsletter"
        verbose_name_plural = "Newsletters"

    def __str__(self):
        return self.correo_electronico



class Contacto(models.Model):
    nombre_contacto = models.CharField("Nombre", max_length=200)
    correo_electronico = models.EmailField("correo electrónico", max_length=200)
    telefono_contacto = models.IntegerField("Teléfono", blank=True)
    sitio_web_contacto = models.URLField("Sitio web", blank=True)
    mensaje_contacto = models.TextField("Mensaje", blank=True)
    fecha_publicacion = models.DateField("Fecha de envío")

    class Meta:
        ordering = ["-fecha_publicacion"]
        verbose_name = "Contacto"
        verbose_name_plural = "Contactos"

    def __str__(self):
        return self.nombre_contacto