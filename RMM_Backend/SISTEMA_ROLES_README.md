# 🔐 Sistema de Roles - Revista Meta Mining

## 📋 Resumen

Se ha implementado un sistema completo de gestión de roles con tres niveles de acceso: **Lector**, **Admin** y **Superusuario**.

---

## 🎯 Roles Implementados

### 1. **LECTOR** (Por defecto)
- ✅ Rol asignado automáticamente al registrarse
- ✅ Puede ver contenido público (Artículos, Blog, Revista)
- ✅ Puede comentar en artículos y blogs
- ✅ Puede dar likes
- ✅ Puede participar en foros
- ❌ NO puede acceder al panel de control
- ❌ NO puede crear/editar/eliminar contenido

### 2. **ADMIN** (Administrador)
- ✅ Puede acceder al panel de control
- ✅ Puede crear, editar y eliminar:
  - Artículos
  - Blogs
  - Ediciones de Revista
- ✅ Puede comentar y dar likes
- ✅ Puede moderar comentarios (editar/eliminar comentarios de otros)
- ✅ Puede participar en foros
- ❌ NO puede asignar roles a otros usuarios
- ❌ NO puede crear superusuarios

### 3. **SUPERUSUARIO**
- ✅ **Acceso total** al sistema
- ✅ Puede hacer todo lo que hace un Admin
- ✅ **Puede asignar roles** (LECTOR o ADMIN) a otros usuarios
- ✅ Acceso al panel de administración de Django
- ✅ Solo se puede crear desde la terminal
- ⚠️  Su rol NO puede ser modificado por nadie

---

## 🛠️ Implementación Backend

### 1. **Modelo User** (`app/users/models.py`)

Se agregó el campo `role` al modelo User:

```python
class User(AbstractUser, TimeStampedModel):
    class Roles(models.TextChoices):
        LECTOR = 'LECTOR', _('Lector')
        ADMIN = 'ADMIN', _('Administrador')
        SUPERUSUARIO = 'SUPERUSUARIO', _('Superusuario')
    
    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.LECTOR,
    )
```

**Métodos útiles agregados:**
- `is_lector()` - Verifica si es Lector
- `is_admin()` - Verifica si es Admin
- `is_superusuario_role()` - Verifica si es Superusuario
- `can_access_panel()` - Verifica si puede acceder al panel
- `can_manage_content()` - Verifica si puede gestionar contenido
- `can_assign_roles()` - Verifica si puede asignar roles

### 2. **Permisos Personalizados** (`app/common/permissions.py`)

Se crearon permisos basados en roles:

| Permiso | Descripción | Uso |
|---------|-------------|-----|
| `IsSuperusuario` | Solo SUPERUSUARIO | Gestión de roles |
| `IsAdminOrSuperusuario` | ADMIN y SUPERUSUARIO | Panel de control |
| `CanManageContent` | Lectura: Todos / Escritura: Admin+ | Artículos, Blog, Revista |
| `CanComment` | Lectura: Todos / Comentar: Autenticados | Comentarios |
| `CanLike` | Solo autenticados | Likes |
| `ReadOnly` | Solo lectura | Endpoints de consulta |

### 3. **ViewSets Protegidos**

#### Artículos (`app/articles/views.py`)
```python
class ArticuloViewSet(viewsets.ModelViewSet):
    permission_classes = [CanManageContent]  # ✅ Protegido

class ComentarioArticuloViewSet(viewsets.ModelViewSet):
    permission_classes = [CanComment]  # ✅ Protegido
```

#### Blog (`app/blog/views.py`)
```python
class BlogViewSet(viewsets.ModelViewSet):
    permission_classes = [CanManageContent]  # ✅ Protegido

class ComentarioBlogViewSet(viewsets.ModelViewSet):
    permission_classes = [CanComment]  # ✅ Protegido
```

#### Revista (`app/magazine/views.py`)
```python
class EdicionesViewSet(viewsets.ModelViewSet):
    permission_classes = [CanManageContent]  # ✅ Protegido
```

### 4. **Endpoints de Gestión de Roles** (`app/users/views.py`)

#### **Asignar Rol** (Solo Superusuario)
```
POST /api/v1/users/roles/assign/

Body:
{
    "user_id": 123,
    "role": "ADMIN"  // o "LECTOR"
}

Response:
{
    "message": "Rol asignado exitosamente",
    "user": {...},
    "previous_role": "LECTOR",
    "new_role": "ADMIN",
    "assigned_by": "admin@example.com"
}
```

#### **Listar Usuarios con Roles** (Solo Superusuario)
```
GET /api/v1/users/roles/users/

Response:
[
    {
        "id": 1,
        "email": "user@example.com",
        "role": "LECTOR",
        ...
    },
    ...
]
```

### 5. **Comando de Terminal para Crear Superusuarios**

Se creó un comando personalizado:

```bash
# Modo interactivo (solicita email y contraseña)
python manage.py createsuperuser_with_role

# Modo no-interactivo (con email)
python manage.py createsuperuser_with_role --email admin@example.com --noinput
```

**Características:**
- ✅ Asigna automáticamente `role = 'SUPERUSUARIO'`
- ✅ Asigna `is_staff = True` y `is_superuser = True`
- ✅ Valida contraseñas (mínimo 8 caracteres)
- ✅ Verifica que el email no exista
- ✅ Modo no-interactivo genera contraseña aleatoria segura

### 6. **Serializer Actualizado** (`app/users/serializers.py`)

Se agregó el campo `role` al UserSerializer:

```python
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        fields = [..., 'role']
        read_only_fields = [..., 'role']  # No se puede modificar directamente
```

---

## 📚 Endpoints API

### **Públicos (Sin autenticación)**
```
GET  /api/v1/articles/articulos/         # Listar artículos
GET  /api/v1/blog/blogs/                 # Listar blogs
GET  /api/v1/magazine/editions/          # Listar ediciones
```

### **Autenticados (Todos los roles)**
```
POST /api/v1/articles/{id}/toggle_like/  # Dar like a artículo
POST /api/v1/blog/{id}/toggle_like/      # Dar like a blog
POST /api/v1/articles/comentarios/       # Crear comentario
POST /api/v1/blog/comentarios/           # Crear comentario
```

### **Admin y Superusuario**
```
POST   /api/v1/articles/articulos/       # Crear artículo
PUT    /api/v1/articles/articulos/{id}/  # Editar artículo
DELETE /api/v1/articles/articulos/{id}/  # Eliminar artículo

POST   /api/v1/blog/blogs/               # Crear blog
PUT    /api/v1/blog/blogs/{id}/          # Editar blog
DELETE /api/v1/blog/blogs/{id}/          # Eliminar blog

POST   /api/v1/magazine/editions/        # Crear edición
PUT    /api/v1/magazine/editions/{id}/   # Editar edición
DELETE /api/v1/magazine/editions/{id}/   # Eliminar edición
```

### **Solo Superusuario**
```
POST /api/v1/users/roles/assign/         # Asignar rol
GET  /api/v1/users/roles/users/          # Listar usuarios con roles
```

---

## 🔍 Verificación de Implementación

### 1. **Verificar campo role en base de datos**
```bash
python manage.py shell

>>> from app.users.models import User
>>> user = User.objects.first()
>>> print(user.role)  # Debe mostrar: LECTOR, ADMIN o SUPERUSUARIO
```

### 2. **Crear un superusuario**
```bash
python manage.py createsuperuser_with_role
# Email: superadmin@example.com
# Contraseña: ********
```

### 3. **Probar permisos**
```bash
# Como Lector: Puede GET, NO puede POST
curl -X GET http://localhost:8000/api/v1/articles/articulos/

# Como Admin/Superusuario: Puede GET y POST
curl -X POST http://localhost:8000/api/v1/articles/articulos/ \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"titulo_articulo": "Test", ...}'
```

---

## 📝 Notas Importantes

1. **Migración de Usuarios Existentes**:
   - Los usuarios existentes tendrán `role = 'LECTOR'` por defecto
   - Un superusuario debe asignarles roles manualmente si es necesario

2. **Protección de Superusuarios**:
   - Los superusuarios solo se crean desde terminal
   - No se puede cambiar el rol de un superusuario via API
   - No se puede cambiar el propio rol

3. **Búsqueda sin Acentos**:
   - Todos los ViewSets protegidos también tienen búsqueda sin acentos
   - Funciona con el filtro `AccentInsensitiveSearchFilter`

4. **Próximos Pasos (Frontend)**:
   - Crear vista de login exclusiva para panel
   - Proteger rutas del panel según rol
   - Implementar redirección automática para Lectores
   - Mostrar/ocultar opciones según rol en UI

---

## 🚀 Estado del Proyecto

### ✅ Backend - COMPLETADO
- [x] Modelo User con campo de roles
- [x] Permisos personalizados
- [x] ViewSets protegidos (Artículos, Blog, Revista)
- [x] Endpoints de gestión de roles
- [x] Comando de terminal para superusuarios
- [x] Serializers actualizados

### ⏳ Frontend - PENDIENTE
- [ ] Vista de login exclusiva para panel
- [ ] Protección de rutas según rol
- [ ] Redirección automática para Lectores
- [ ] UI adaptada según rol

---

## 📞 Soporte

Para más información sobre el sistema de roles, consulta:
- Permisos: `app/common/permissions.py`
- Modelos: `app/users/models.py`
- Endpoints: `app/users/views.py`
- Comando: `app/users/management/commands/createsuperuser_with_role.py`

