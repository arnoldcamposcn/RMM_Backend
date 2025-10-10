# 🔍 Filtros de Búsqueda Sin Acentos

## Resumen

Sistema de búsqueda que ignora acentos usando la librería **Unidecode**, permitiendo búsquedas más flexibles.

## ✨ Características

- Buscar "tecnologia" encuentra "tecnología"
- Buscar "minería" encuentra "mineria"
- Bidireccional y case-insensitive

## 📊 ViewSets Implementados

- ✅ `ArticuloViewSet` - Artículos
- ✅ `ComentarioArticuloViewSet` - Comentarios de artículos
- ✅ `BlogViewSet` - Blogs
- ✅ `ComentarioBlogViewSet` - Comentarios de blogs
- ✅ `EdicionesViewSet` - Ediciones de revista

## 🚀 Uso

```python
from app.common.filters import AccentInsensitiveSearchFilter

class MiViewSet(viewsets.ModelViewSet):
    filter_backends = [AccentInsensitiveSearchFilter]
    search_fields = ['titulo', 'contenido']
```

## 📝 Implementación

📁 `app/common/filters.py` - Clase `AccentInsensitiveSearchFilter`

