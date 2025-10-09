# Filtros Personalizados

## 🔍 AccentInsensitiveSearchFilter

Filtro de búsqueda que ignora acentos y diacríticos, permitiendo búsquedas más flexibles e intuitivas para los usuarios.

### 📦 Dependencias

Este filtro requiere la librería `Unidecode`:

```bash
pip install Unidecode
```

### ✨ Características

- **Búsqueda sin acentos**: Normaliza tanto el término de búsqueda como el contenido
- **Bidireccional**: Funciona sin importar si el usuario escribe con o sin acentos
- **Compatible con DRF**: Extiende el `SearchFilter` estándar de Django REST Framework
- **Fácil integración**: Solo cambia una línea de código en tu ViewSet

### 🎯 Ejemplos de uso

#### Búsquedas que funcionan:

| Usuario busca | Encuentra artículos con |
|---------------|-------------------------|
| `tecnologia` | "tecnología", "tecnologia" |
| `minería` | "minería", "mineria" |
| `año` | "año", "ano" |
| `comunicacion` | "comunicación", "comunicacion" |

### 💻 Implementación

#### 1. Importar el filtro en tu ViewSet:

```python
from app.common.filters import AccentInsensitiveSearchFilter
```

#### 2. Usar el filtro en lugar del SearchFilter estándar:

```python
class ArticuloViewSet(viewsets.ModelViewSet):
    queryset = Articulos.objects.all()
    serializer_class = ArticuloSerializer
    
    # ✅ Usar AccentInsensitiveSearchFilter
    filter_backends = [AccentInsensitiveSearchFilter]
    search_fields = ['titulo_articulo', 'contenido']
```

#### 3. Hacer llamadas a la API:

```bash
# Todas estas búsquedas encontrarán artículos con "tecnología"
GET /api/v1/articles/?search=tecnologia
GET /api/v1/articles/?search=tecnología
GET /api/v1/articles/?search=TECNOLOGIA
```

### 🏗️ Arquitectura

El filtro funciona en tres pasos:

1. **Normalización del término de búsqueda**: Usa `unidecode()` para convertir el texto a ASCII
   ```python
   "minería" → "mineria"
   "tecnología" → "tecnologia"
   ```

2. **Normalización del contenido**: Aplica la misma transformación a cada campo del modelo

3. **Comparación**: Compara los textos normalizados (sin acentos) para encontrar coincidencias

### 📊 ViewSets que usan este filtro

#### ✅ Implementados:
- `ArticuloViewSet` - Búsqueda en artículos (título y contenido)
- `ComentarioArticuloViewSet` - Búsqueda en comentarios de artículos
- `BlogViewSet` - Búsqueda en blogs (título y contenido)
- `ComentarioBlogViewSet` - Búsqueda en comentarios de blogs
- `EdicionesViewSet` - Búsqueda en ediciones de revista (título y contenido)

#### 🔄 Próximos a implementar:
- `ForoViewSet` - Búsqueda en temas del foro (si aplica)

### 🔧 Personalización

Si necesitas modificar el comportamiento del filtro, puedes extenderlo:

```python
from app.common.filters import AccentInsensitiveSearchFilter

class MiFilterPersonalizado(AccentInsensitiveSearchFilter):
    def filter_queryset(self, request, queryset, view):
        # Tu lógica personalizada aquí
        queryset = super().filter_queryset(request, queryset, view)
        # Más filtros personalizados...
        return queryset
```

### ⚡ Rendimiento

- **Tamaño de dataset pequeño-mediano** (< 10,000 registros): Excelente rendimiento
- **Tamaño de dataset grande** (> 10,000 registros): Considera usar PostgreSQL con la extensión `unaccent` para mejor rendimiento

### 📝 Notas técnicas

- El filtro es **case-insensitive** (no distingue mayúsculas/minúsculas)
- Mantiene la compatibilidad con otros filtros de DRF (puedes combinarlos)
- No modifica los datos en la base de datos, solo normaliza durante la búsqueda

### 🐛 Solución de problemas

**Problema**: El filtro no funciona
- **Solución**: Verifica que `Unidecode` esté instalado: `pip list | grep -i unidecode`

**Problema**: Los resultados no son los esperados
- **Solución**: Verifica que `search_fields` contenga los campos correctos del modelo

**Problema**: Error de importación
- **Solución**: Asegúrate de que la ruta de importación sea correcta: `from app.common.filters import AccentInsensitiveSearchFilter`

