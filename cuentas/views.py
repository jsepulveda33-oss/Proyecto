from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect, render

from .forms import InicioSesionForm, RegistroForm


def registro(request):
    if request.user.is_authenticated:
        return redirect("cuentas:perfil")

    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            messages.success(
                request, f"¡Hola, {usuario.first_name}! Tu cuenta fue creada con éxito."
            )
            return redirect("cuentas:perfil")
        messages.error(request, "Revisa los datos marcados en el formulario.")
    else:
        form = RegistroForm()

    return render(request, "cuentas/registro.html", {"form": form})


class IniciarSesionView(SuccessMessageMixin, LoginView):
    template_name = "cuentas/login.html"
    authentication_form = InicioSesionForm
    redirect_authenticated_user = True
    success_message = "Iniciaste sesión correctamente."

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        if not self.request.POST.get("recordarme"):
            # Sin "Mantener sesión iniciada", la sesión termina al cerrar el navegador.
            self.request.session.set_expiry(0)
        return respuesta


class CerrarSesionView(LogoutView):
    def post(self, request, *args, **kwargs):
        respuesta = super().post(request, *args, **kwargs)
        messages.info(request, "Cerraste sesión. ¡Vuelve pronto!")
        return respuesta


@login_required
def perfil(request):
    return render(request, "cuentas/perfil.html")
