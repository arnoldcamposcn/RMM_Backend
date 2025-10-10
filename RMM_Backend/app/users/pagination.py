"""
Configuración de paginación para usuarios.
"""

from rest_framework.pagination import PageNumberPagination


class UsersPagination(PageNumberPagination):
    """
    Paginación personalizada para lista de usuarios.
    
    Muestra 50 usuarios por página por defecto.
    Permite al cliente especificar hasta 100 usuarios por página.
    """
    page_size = 8 # Mostrar 50 usuarios por defecto
    page_size_query_param = 'page_size'  # Permitir al cliente cambiar el tamaño
    max_page_size = 8  # Máximo 100 usuarios por página

