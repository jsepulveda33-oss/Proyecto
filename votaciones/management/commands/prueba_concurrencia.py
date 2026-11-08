import threading

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.management.base import BaseCommand, CommandError
from django.db import connections
from django.db.models import F
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from votaciones.models import Opcion, Voto, Votacion

USUARIOS = ("votante1", "votante2")


def _disparar(cliente, url, datos, barrera, resultados, indice):
    """Envía un POST en el mismo instante que la otra hebra."""
    try:
        barrera.wait(timeout=10)
        resp = cliente.post(url, datos)
        mensajes = [str(m) for m in get_messages(resp.wsgi_request)]
        resultados[indice] = (resp.status_code, mensajes)
    except Exception as exc:
        resultados[indice] = ("ERROR", [repr(exc)])
    finally:
        connections.close_all()


class Command(BaseCommand):
    help = "CP-09: solicitudes de voto simultáneas contra la base de datos real."

    def add_arguments(self, parser):
        parser.add_argument(
            "--conservar", action="store_true",
            help="No borra los votos de prueba al terminar.",
        )

    def _limpiar(self, usuarios, categoria, edicion):
        for voto in Voto.objects.filter(
            usuario__in=usuarios, categoria=categoria, edicion=edicion
        ):
            Opcion.objects.filter(pk=voto.opcion_id, votos__gt=0).update(
                votos=F("votos") - 1
            )
            voto.delete()

    def _escenario(self, titulo, quienes, categoria, edicion, opcion, url, datos, esperado):
        self.stdout.write(self.style.MIGRATE_LABEL(f"Escenario {titulo}"))
        usuarios = list(set(quienes))
        self._limpiar(usuarios, categoria, edicion)
        antes = Opcion.objects.get(pk=opcion.pk).votos

        clientes = []
        for u in quienes:
            c = Client(HTTP_HOST="127.0.0.1")
            c.force_login(u)
            clientes.append(c)

        barrera = threading.Barrier(len(clientes))
        resultados = [None] * len(clientes)
        hilos = [
            threading.Thread(
                target=_disparar, args=(c, url, datos, barrera, resultados, i)
            )
            for i, c in enumerate(clientes)
        ]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join()

        for i, (estado, mensajes) in enumerate(resultados, 1):
            self.stdout.write(f"  Solicitud {i} -> {estado} {mensajes}")

        guardados = Voto.objects.filter(
            usuario__in=usuarios, categoria=categoria, edicion=edicion
        ).count()
        aumento = Opcion.objects.get(pk=opcion.pk).votos - antes
        self.stdout.write(f"  Votos guardados en la tabla Voto: {guardados} (esperado {esperado})")
        self.stdout.write(f"  Aumento del contador de la opción: {aumento} (esperado {esperado})")
        ok = guardados == esperado and aumento == esperado
        if ok:
            self.stdout.write(self.style.SUCCESS("  RESULTADO: PASA\n"))
        else:
            self.stdout.write(self.style.ERROR("  RESULTADO: FALLA\n"))
        return ok

    def handle(self, *args, **opts):
        User = get_user_model()
        usuarios = list(User.objects.filter(username__in=USUARIOS).order_by("username"))
        if len(usuarios) < 2:
            raise CommandError(
                "Faltan usuarios de prueba. Ejecuta primero: "
                "python manage.py crear_usuarios_prueba"
            )
        u1, u2 = usuarios[0], usuarios[1]

        ahora = timezone.now()
        votacion = None
        for v in Votacion.objects.filter(
            activa=True, fecha_inicio__lte=ahora, fecha_fin__gte=ahora
        ).select_related("categoria__edicion"):
            if v.opciones.exists():
                votacion = v
                break
        if votacion is None:
            raise CommandError(
                "No hay una votación activa con opciones. Carga los datos: "
                "python manage.py loaddata datos_iniciales"
            )

        categoria = votacion.categoria
        edicion = categoria.edicion
        opcion = votacion.opciones.first()
        url = reverse("votar", args=[categoria.pk])
        datos = {"opcion": opcion.pk, "votacion": votacion.pk}

        self.stdout.write(self.style.MIGRATE_HEADING("=== CP-09: concurrencia al votar ==="))
        self.stdout.write(f"Categoría: {categoria.nombre} | Opción: {opcion.nombre}\n")

        ok_a = self._escenario(
            "A: el MISMO usuario envía 2 votos a la vez",
            [u1, u1], categoria, edicion, opcion, url, datos, esperado=1,
        )
        ok_b = self._escenario(
            "B: DOS usuarios distintos votan por la misma opción a la vez",
            [u1, u2], categoria, edicion, opcion, url, datos, esperado=2,
        )

        if not opts["conservar"]:
            self._limpiar([u1, u2], categoria, edicion)
            self.stdout.write("Votos de prueba eliminados y contadores restaurados.")

        if ok_a and ok_b:
            self.stdout.write(self.style.SUCCESS("CP-09 COMPLETO: PASA"))
        else:
            self.stdout.write(self.style.ERROR("CP-09 COMPLETO: FALLA"))