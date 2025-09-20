from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User    

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ("id", "email", "first_name", "last_name", "is_active", "fecha_creacion")
    list_filter = ("is_active", "is_staff", "perfil_completo", "genero", "pais")
    ordering = ("-fecha_creacion",)
    readonly_fields = ("fecha_creacion", "fecha_actualizacion", "edad")
    
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Información Personal", {"fields": ("first_name", "last_name", "fecha_nacimiento", "edad", "genero", "pais", "ciudad", "telefono")}),
        ("Perfil", {"fields": ("usuario_unico", "biografia", "perfil_url", "facebook_url", "linkedin_url")}),
        ("Configuración", {"fields": ("perfil_completo",)}),
        ("Permisos", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Fechas Importantes", {"fields": ("last_login", "date_joined", "fecha_creacion", "fecha_actualizacion")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "first_name", "last_name")
        }),
    )
    search_fields = ("email", "first_name", "last_name", "usuario_unico")
    filter_horizontal = ("groups", "user_permissions")
