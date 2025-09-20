from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.

class TimeStampedModel(models.Model):
    """
    Modelo abstracto que proporciona campos de timestamping automático
    """
    fecha_creacion = models.DateTimeField(
        _('Fecha de creación'),
        auto_now_add=True,
        help_text=_('Fecha y hora en que se creó el registro')
    )
    fecha_actualizacion = models.DateTimeField(
        _('Fecha de actualización'),
        auto_now=True,
        help_text=_('Fecha y hora de la última actualización del registro')
    )
    

    class Meta:
        abstract = True
        ordering = ['-fecha_creacion']

