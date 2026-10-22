from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()

CLAVE = "Acordeon-2027!"


class RegistroTests(TestCase):
    def datos(self, **cambios):
        datos = {
            "username": "nuevo",
            "first_name": "Ana",
            "last_name": "Pérez",
            "email": "ana@ejemplo.com",
            "password1": CLAVE,
            "password2": CLAVE,
            "acepta_reglamento": "on",
        }
        datos.update(cambios)
        return datos

    def test_muestra_formulario(self):
        respuesta = self.client.get(reverse("cuentas:registro"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Completar registro")

    def test_registro_crea_usuario_e_inicia_sesion(self):
        respuesta = self.client.post(
            reverse("cuentas:registro"), self.datos(), follow=True
        )
        self.assertRedirects(respuesta, reverse("cuentas:perfil"))
        self.assertTrue(User.objects.filter(username="nuevo").exists())
        self.assertTrue(respuesta.context["user"].is_authenticated)
        self.assertContains(respuesta, "Tu cuenta fue creada con éxito")

    def test_contrasenas_distintas_muestran_error(self):
        respuesta = self.client.post(
            reverse("cuentas:registro"), self.datos(password2="otra-clave-123")
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(User.objects.filter(username="nuevo").exists())
        self.assertTrue(respuesta.context["form"].has_error("password2"))
        self.assertContains(respuesta, "Revisa los datos marcados")

    def test_reglamento_es_obligatorio(self):
        datos = self.datos()
        del datos["acepta_reglamento"]
        respuesta = self.client.post(reverse("cuentas:registro"), datos)
        self.assertContains(respuesta, "Debes aceptar el reglamento para registrarte.")
        self.assertFalse(User.objects.filter(username="nuevo").exists())

    def test_correo_repetido_muestra_error(self):
        User.objects.create_user("otro", "ana@ejemplo.com", CLAVE)
        respuesta = self.client.post(reverse("cuentas:registro"), self.datos())
        self.assertContains(respuesta, "Ya existe una cuenta con este correo.")
        self.assertFalse(User.objects.filter(username="nuevo").exists())


class SesionTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user("angie", "angie@ejemplo.com", CLAVE)

    def test_inicio_de_sesion_correcto(self):
        respuesta = self.client.post(
            reverse("cuentas:login"),
            {"username": "angie", "password": CLAVE},
            follow=True,
        )
        self.assertRedirects(respuesta, reverse("cuentas:perfil"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.usuario.pk)
        self.assertContains(respuesta, "Iniciaste sesión correctamente.")

    def test_sin_recordarme_la_sesion_termina_al_cerrar_el_navegador(self):
        self.client.post(
            reverse("cuentas:login"), {"username": "angie", "password": CLAVE}
        )
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_con_recordarme_la_sesion_se_mantiene(self):
        self.client.post(
            reverse("cuentas:login"),
            {"username": "angie", "password": CLAVE, "recordarme": "on"},
        )
        self.assertFalse(self.client.session.get_expire_at_browser_close())

    def test_inicio_de_sesion_incorrecto(self):
        respuesta = self.client.post(
            reverse("cuentas:login"), {"username": "angie", "password": "mala"}
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertTrue(respuesta.context["form"].non_field_errors())

    def test_cierre_de_sesion(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.post(reverse("cuentas:logout"), follow=True)
        self.assertRedirects(respuesta, reverse("cuentas:login"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertContains(respuesta, "Cerraste sesión.")

    def test_perfil_exige_sesion(self):
        respuesta = self.client.get(reverse("cuentas:perfil"))
        self.assertRedirects(
            respuesta,
            f"{reverse('cuentas:login')}?next={reverse('cuentas:perfil')}",
        )

    def test_perfil_muestra_datos_del_usuario(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.get(reverse("cuentas:perfil"))
        self.assertContains(respuesta, "angie@ejemplo.com")
