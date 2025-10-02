from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from app.common.models import TimeStampedModel
from datetime import date
from django.utils.translation import gettext_lazy as _
import re


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio")
        email = self.normalize_email(email)
        
        # Generar usuario_unico si no se proporciona
        if 'usuario_unico' not in extra_fields or not extra_fields['usuario_unico']:
            # Crear un usuario temporal para generar el usuario_unico
            temp_user = self.model(email=email, **extra_fields)
            extra_fields['usuario_unico'] = temp_user.generar_usuario_unico()
        
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser, TimeStampedModel):
    username = None  # Usaremos el email como username
    email = models.EmailField(unique=True)
    
    # Datos extra
    biografia = models.TextField(null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    genero = models.CharField(max_length=20, null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    pais = models.CharField(max_length=100, null=True, blank=True)
    ciudad = models.CharField(max_length=100, null=True, blank=True)

    # Redes sociales
    perfil_url = models.URLField(max_length=300, null=True, blank=True)
    facebook_url = models.URLField(max_length=300, null=True, blank=True)
    linkedin_url = models.URLField(max_length=300, null=True, blank=True)

    # Estado
    perfil_completo = models.BooleanField(
        _('Perfil completo'),
        default=False,
        help_text=_('Indica si el usuario completó su perfil')
    )

    # Usuario público único
    usuario_unico = models.CharField(
        _('Usuario único'),
        max_length=100,
        unique=True,
        null=False,
        blank=True,
        help_text=_('Nombre de usuario único (nickname público)')
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        db_table = 'users'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return self.email

    @property
    def edad(self):
        """Calcula la edad dinámicamente"""
        if self.fecha_nacimiento:
            today = date.today()
            return today.year - self.fecha_nacimiento.year - (
                (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
            )
        return None

    def verificar_perfil_completo(self, save=True):
        """Verifica si el perfil está completo"""
        campos_obligatorios = [
            self.first_name,
            self.last_name,
            self.fecha_nacimiento,
            self.usuario_unico,
            self.pais
        ]
        self.perfil_completo = all(campo for campo in campos_obligatorios)
        if save:
            self.save(update_fields=['perfil_completo'])

    def generar_usuario_unico(self, base_username=None):
        """Genera un nickname único"""
        if not base_username:
            if self.first_name and self.last_name:
                base_username = f"{self.first_name.lower()}.{self.last_name.lower()}"
            else:
                base_username = self.email.split('@')[0].lower()

        base_username = re.sub(r'[^a-z0-9._]', '', base_username)
        counter = 1
        unique_username = base_username

        while User.objects.filter(usuario_unico=unique_username).exclude(id=self.id).exists():
            unique_username = f"{base_username}{counter}"
            counter += 1

        return unique_username
