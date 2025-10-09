"""
Filtros personalizados para búsqueda sin acentos usando Unidecode.

Este módulo proporciona un filtro de búsqueda que normaliza
tanto el término de búsqueda como el contenido, permitiendo
búsquedas que ignoren acentos y diacríticos.
"""

from rest_framework import filters
from django.db.models import Q
from unidecode import unidecode


class AccentInsensitiveSearchFilter(filters.SearchFilter):
    """
    Filtro de búsqueda que ignora acentos y diacríticos usando Unidecode.
    
    Normaliza tanto el término de búsqueda como el contenido de la base de datos
    para permitir coincidencias sin importar los acentos.
    
    Ejemplos:
        - Buscar "tecnologia" encontrará "tecnología" y "tecnologia"
        - Buscar "minería" encontrará "mineria" y "minería"
        - Buscar "año" encontrará "año" y "ano"
    
    Uso en ViewSet:
        class ArticuloViewSet(viewsets.ModelViewSet):
            filter_backends = [AccentInsensitiveSearchFilter]
            search_fields = ['titulo_articulo', 'contenido']
    """
    
    def filter_queryset(self, request, queryset, view):
        """
        Filtra el queryset aplicando normalización de acentos con Unidecode.
        
        Args:
            request: HttpRequest con el parámetro de búsqueda
            queryset: QuerySet inicial a filtrar
            view: Vista que utiliza el filtro
            
        Returns:
            QuerySet filtrado con resultados que coinciden sin importar acentos
        """
        search_fields = self.get_search_fields(view, request)
        search_terms = self.get_search_terms(request)
        
        if not search_fields or not search_terms:
            return queryset
        
        # Obtener el término de búsqueda original
        search_param = request.query_params.get(self.search_param, '')
        
        if not search_param:
            return queryset
        
        # Normalizar el término de búsqueda (remover acentos)
        normalized_search = unidecode(search_param).lower()
        
        # Crear lista de IDs que coinciden
        matching_ids = []
        
        for obj in queryset:
            match_found = False
            
            # Revisar cada campo de búsqueda
            for search_field in search_fields:
                if match_found:
                    break
                
                # Obtener el valor del campo
                field_value = self.get_field_value(obj, search_field)
                
                if field_value:
                    # Normalizar el valor del campo (remover acentos)
                    normalized_field = unidecode(str(field_value)).lower()
                    
                    # Verificar si el término de búsqueda está en el campo
                    if normalized_search in normalized_field:
                        matching_ids.append(obj.pk)
                        match_found = True
        
        # Filtrar el queryset por los IDs que coinciden
        if matching_ids:
            return queryset.filter(pk__in=matching_ids).distinct()
        
        return queryset.none()
    
    def get_field_value(self, obj, field_path):
        """
        Obtiene el valor de un campo, incluso si es una relación anidada.
        
        Args:
            obj: Objeto del modelo
            field_path: Ruta del campo (ej: 'titulo' o 'autor__nombre')
            
        Returns:
            Valor del campo o None si no existe
        """
        try:
            # Manejar campos anidados (ej: 'autor__nombre')
            fields = field_path.split('__')
            value = obj
            
            for field in fields:
                if hasattr(value, field):
                    value = getattr(value, field)
                else:
                    return None
            
            return value
        except (AttributeError, TypeError):
            return None

