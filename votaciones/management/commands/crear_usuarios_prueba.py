from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

USUARIOS = ["votante1", "votante2", "votante3", "votante4"]
CLAVE = "Prueba12345"


class Command(BaseCommand):
    help = "Crea 4 usuarios ficticios de prueba (solo para desarrollo local)."

    def handle(self, *args, **options):
        User = get_user_model()
        for nombre in USUARIOS:
            user, creado = User.objects.get_or_create(
                username=nombre,
                defaults={"email": f"{nombre}@example.com"},
            )
            user.set_password(CLAVE)
            user.save()
            self.stdout.write(f"{nombre}: {'creado' if creado else 'actualizado'}")
        self.stdout.write(self.style.SUCCESS(f"Contraseña de prueba: {CLAVE}"))