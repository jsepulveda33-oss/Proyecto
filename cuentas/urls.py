from django.urls import path

from . import views

app_name = "cuentas"

urlpatterns = [
    path("registro/", views.registro, name="registro"),
    path("iniciar-sesion/", views.IniciarSesionView.as_view(), name="login"),
    path("cerrar-sesion/", views.CerrarSesionView.as_view(), name="logout"),
    path("perfil/", views.perfil, name="perfil"),
]
