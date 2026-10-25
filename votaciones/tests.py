
from django.test import TestCase
from django.urls import reverse

from .models import Categoria, Edicion, Opcion, Votacion


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
