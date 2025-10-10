"""
Permisos personalizados para el sistema de roles.

Este módulo define los permisos basados en roles para controlar
el acceso a diferentes partes del sistema.

Roles:
- LECTOR: Acceso solo lectura, puede comentar y dar likes
- ADMIN: Puede gestionar contenido (crear, editar, eliminar)
- SUPERUSUARIO: Acceso total + gestión de roles
"""

from rest_framework import permissions


class IsSuperusuario(permissions.BasePermission):
    """
    Permiso que solo permite acceso a usuarios con rol SUPERUSUARIO.
    
    Uso típico: Endpoints de gestión de roles y configuración del sistema.
    """
    message = "Solo los superusuarios pueden realizar esta acción."
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == 'SUPERUSUARIO'
        )


class IsAdminOrSuperusuario(permissions.BasePermission):
    """
    Permiso que permite acceso a ADMIN y SUPERUSUARIO.
    
    Uso típico: Panel de control, gestión de contenido.
    """
    message = "Se requiere rol de Administrador o Superusuario."
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['ADMIN', 'SUPERUSUARIO']
        )


class CanManageContent(permissions.BasePermission):
    """
    Permiso para gestionar contenido (Artículos, Blog, Revistas).
    
    - Lectura (GET, HEAD, OPTIONS): Todos pueden leer
    - Escritura (POST, PUT, PATCH, DELETE): Solo ADMIN y SUPERUSUARIO
    """
    message = "No tienes permisos para gestionar este contenido."
    
    def has_permission(self, request, view):
        # Permitir lectura a todos
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Escritura solo para ADMIN y SUPERUSUARIO
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['ADMIN', 'SUPERUSUARIO']
        )


class CanComment(permissions.BasePermission):
    """
    Permiso para comentar en artículos, blogs y foros.
    
    - Lectura: Todos
    - Crear comentario: Usuarios autenticados (todos los roles)
    - Editar/Eliminar: Solo el autor del comentario o ADMIN/SUPERUSUARIO
    """
    message = "Debes iniciar sesión para comentar."
    
    def has_permission(self, request, view):
        # Permitir lectura a todos
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Crear comentarios: cualquier usuario autenticado
        if request.method == 'POST':
            return request.user and request.user.is_authenticated
        
        # PUT, PATCH, DELETE requieren verificación del objeto
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Lectura: Todos
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # El autor puede editar/eliminar su propio comentario
        if hasattr(obj, 'autor') and obj.autor == request.user:
            return True
        
        # ADMIN y SUPERUSUARIO pueden editar/eliminar cualquier comentario
        return request.user.role in ['ADMIN', 'SUPERUSUARIO']


class CanLike(permissions.BasePermission):
    """
    Permiso para dar likes.
    
    Solo usuarios autenticados pueden dar likes (todos los roles).
    """
    message = "Debes iniciar sesión para dar like."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class ReadOnly(permissions.BasePermission):
    """
    Permiso de solo lectura.
    
    Permite solo métodos seguros (GET, HEAD, OPTIONS).
    """
    message = "Esta es una operación de solo lectura."
    
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS

