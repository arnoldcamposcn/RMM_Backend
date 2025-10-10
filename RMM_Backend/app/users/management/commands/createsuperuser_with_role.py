"""
Comando personalizado para crear un superusuario con rol SUPERUSUARIO.

Este comando extiende el comportamiento del comando createsuperuser de Django
para asignar automáticamente el rol SUPERUSUARIO al usuario creado.

Uso:
    python manage.py createsuperuser_with_role
    
El comando solicitará:
    - Email
    - Contraseña (con confirmación)

El usuario creado tendrá:
    - is_staff = True
    - is_superuser = True
    - role = 'SUPERUSUARIO'
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import IntegrityError
import getpass

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea un superusuario con rol SUPERUSUARIO para el panel de control'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            dest='email',
            default=None,
            help='Email del superusuario',
        )
        parser.add_argument(
            '--noinput',
            action='store_true',
            dest='no_input',
            help='No solicitar entrada del usuario (requiere --email)',
        )
    
    def handle(self, *args, **options):
        email = options.get('email')
        no_input = options.get('no_input', False)
        
        # Si no se proporciona email y no está en modo no-input, solicitarlo
        if not email and not no_input:
            email = input('Email del superusuario: ').strip()
        
        if not email:
            raise CommandError('Se requiere un email para crear el superusuario.')
        
        # Validar que el email no exista
        if User.objects.filter(email=email).exists():
            raise CommandError(f'Ya existe un usuario con el email {email}')
        
        # Solicitar contraseña si no está en modo no-input
        if not no_input:
            password = None
            while not password:
                password = getpass.getpass('Contraseña: ')
                password2 = getpass.getpass('Contraseña (confirmación): ')
                
                if password != password2:
                    self.stdout.write(
                        self.style.ERROR('Las contraseñas no coinciden. Intenta nuevamente.')
                    )
                    password = None
                elif len(password) < 8:
                    self.stdout.write(
                        self.style.ERROR('La contraseña debe tener al menos 8 caracteres.')
                    )
                    password = None
        else:
            # En modo no-input, generar una contraseña aleatoria
            import secrets
            import string
            alphabet = string.ascii_letters + string.digits + string.punctuation
            password = ''.join(secrets.choice(alphabet) for i in range(16))
            self.stdout.write(
                self.style.WARNING(f'Contraseña generada automáticamente: {password}')
            )
            self.stdout.write(
                self.style.WARNING('¡Guarda esta contraseña de forma segura!')
            )
        
        try:
            # Crear el superusuario con rol SUPERUSUARIO
            user = User.objects.create_superuser(
                email=email,
                password=password
            )
            
            # El role ya se asigna automáticamente en create_superuser,
            # pero lo verificamos por seguridad
            if user.role != 'SUPERUSUARIO':
                user.role = 'SUPERUSUARIO'
                user.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Superusuario creado exitosamente!')
            )
            self.stdout.write(
                self.style.SUCCESS(f'   Email: {user.email}')
            )
            self.stdout.write(
                self.style.SUCCESS(f'   Rol: {user.get_role_display()}')
            )
            self.stdout.write(
                self.style.SUCCESS(f'   is_staff: {user.is_staff}')
            )
            self.stdout.write(
                self.style.SUCCESS(f'   is_superuser: {user.is_superuser}')
            )
            self.stdout.write('')
            self.stdout.write(
                self.style.WARNING('⚠️  Este usuario tiene acceso total al sistema y puede:')
            )
            self.stdout.write('   - Acceder al panel de administración de Django')
            self.stdout.write('   - Gestionar roles de otros usuarios')
            self.stdout.write('   - Crear, editar y eliminar contenido (Artículos, Blog, Revista)')
            self.stdout.write('   - Acceder al panel de control frontend')
            
        except IntegrityError as e:
            raise CommandError(f'Error al crear el superusuario: {e}')
        except Exception as e:
            raise CommandError(f'Error inesperado: {e}')

