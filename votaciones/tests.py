
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Categoria, Edicion, Opcion, Voto, Votacion


class InterfazPublicaTests(TestCase):
    fixtures = ["datos_iniciales"]

    def test_inicio_responde(self):
        r = self.client.get(reverse("inicio"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Festival de la Leyenda Vallenata")

    def test_lista_de_ediciones(self):
        r = self.client.get(reverse("ediciones"))
        self.assertEqual(r.status_code, 200)
        for edicion in Edicion.objects.all():
            self.assertContains(r, edicion.nombre)

    def test_categorias_de_una_edicion(self):
        edicion = Edicion.objects.first()
        r = self.client.get(reverse("edicion_detalle", args=[edicion.pk]))
        self.assertEqual(r.status_code, 200)
        for categoria in edicion.categorias.all():
            self.assertContains(r, categoria.nombre)

    def test_votaciones_de_una_categoria(self):
        categoria = Categoria.objects.first()
        r = self.client.get(reverse("categoria_detalle", args=[categoria.pk]))
        self.assertEqual(r.status_code, 200)
        for votacion in categoria.votaciones.all():
            self.assertContains(r, votacion.nombre)

    def test_opciones_de_una_votacion(self):
        votacion = Votacion.objects.first()
        r = self.client.get(reverse("votacion_detalle", args=[votacion.pk]))
        self.assertEqual(r.status_code, 200)
        for opcion in votacion.opciones.all():
            self.assertContains(r, opcion.nombre)

    def test_el_conteo_de_votos_no_se_muestra(self):
        """Los votos acumulados no deben verse en esta etapa (los resultados son de otra entrega)."""
        opcion = Opcion.objects.first()
        r = self.client.get(reverse("votacion_detalle", args=[opcion.votacion_id]))
        self.assertNotContains(r, "votos")

    def test_id_inexistente_da_404(self):
        r = self.client.get(reverse("votacion_detalle", args=[999999]))
        self.assertEqual(r.status_code, 404)


class NucleoVotoTests(TestCase):
    """Pruebas del núcleo del voto (Compañero 1): CP-01 a CP-06, CP-09 y CSRF."""

    def setUp(self):
        U = get_user_model()
        self.user = U.objects.create_user("ana", password="clave-segura-123")
        self.edicion = Edicion.objects.create(
            nombre="Festival", anio=2099, fecha_inicio="2099-01-01",
            fecha_fin="2099-12-31", activa=True,
        )
        self.cat1 = Categoria.objects.create(edicion=self.edicion, nombre="Cat 1")
        self.cat2 = Categoria.objects.create(edicion=self.edicion, nombre="Cat 2")
        ahora = timezone.now()
        self.vot1 = Votacion.objects.create(
            categoria=self.cat1, nombre="V1", activa=True,
            fecha_inicio=ahora - timedelta(days=1), fecha_fin=ahora + timedelta(days=1),
        )
        self.vot2 = Votacion.objects.create(
            categoria=self.cat2, nombre="V2", activa=True,
            fecha_inicio=ahora - timedelta(days=1), fecha_fin=ahora + timedelta(days=1),
        )
        self.op1 = Opcion.objects.create(votacion=self.vot1, nombre="A")
        self.op1b = Opcion.objects.create(votacion=self.vot1, nombre="B")
        self.op2 = Opcion.objects.create(votacion=self.vot2, nombre="C")
        self.client.login(username="ana", password="clave-segura-123")
        self.url1 = reverse("votar", args=[self.cat1.pk])

    def test_cp01_voto_valido(self):
        r = self.client.post(self.url1, {"opcion": self.op1.pk})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Voto.objects.count(), 1)
        self.op1.refresh_from_db()
        self.assertEqual(self.op1.votos, 1)

    def test_cp04_requiere_login(self):
        r = Client().post(self.url1, {"opcion": self.op1.pk})
        self.assertEqual(r.status_code, 302)
        self.assertIn("login", r.url)
        self.assertEqual(Voto.objects.count(), 0)

    def test_cp02_no_permite_votar_dos_veces(self):
        self.client.post(self.url1, {"opcion": self.op1.pk})
        self.client.post(self.url1, {"opcion": self.op1b.pk})
        self.assertEqual(Voto.objects.count(), 1)
        self.op1b.refresh_from_db()
        self.assertEqual(self.op1b.votos, 0)

    def test_cp03_puede_votar_en_otra_categoria(self):
        self.client.post(self.url1, {"opcion": self.op1.pk})
        self.client.post(reverse("votar", args=[self.cat2.pk]), {"opcion": self.op2.pk})
        self.assertEqual(Voto.objects.count(), 2)

    def test_cp05_votacion_no_habilitada(self):
        self.vot1.activa = False
        self.vot1.save()
        self.client.post(self.url1, {"opcion": self.op1.pk})
        self.assertEqual(Voto.objects.count(), 0)

    def test_votacion_cerrada_no_permite_votar(self):
        self.vot1.fecha_fin = timezone.now() - timedelta(hours=1)
        self.vot1.save()
        self.client.post(self.url1, {"opcion": self.op1.pk})
        self.assertEqual(Voto.objects.count(), 0)

    def test_cp06_opcion_de_otra_categoria(self):
        self.client.post(self.url1, {"opcion": self.op2.pk})
        self.assertEqual(Voto.objects.count(), 0)

    def test_sin_opcion_no_registra(self):
        self.client.post(self.url1, {})
        self.assertEqual(Voto.objects.count(), 0)

    def test_get_no_registra_voto(self):
        r = self.client.get(self.url1)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Voto.objects.count(), 0)

    def test_csrf_se_exige(self):
        c = Client(enforce_csrf_checks=True)
        c.login(username="ana", password="clave-segura-123")
        r = c.post(self.url1, {"opcion": self.op1.pk})
        self.assertEqual(r.status_code, 403)
        self.assertEqual(Voto.objects.count(), 0)

    def test_cp09_restriccion_unica_en_bd(self):
        """Simula la carrera: saltándose el formulario, la BD rechaza el duplicado."""
        kwargs = dict(usuario=self.user, edicion=self.edicion, categoria=self.cat1, opcion=self.op1)
        Voto.objects.create(**kwargs)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Voto.objects.create(**kwargs)
        self.assertEqual(Voto.objects.count(), 1)