from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm


class RegistroForm(UserCreationForm):
    first_name = forms.CharField(label="Nombre", max_length=150)
    last_name = forms.CharField(label="Apellido", max_length=150)
    email = forms.EmailField(label="Correo electrónico")
    acepta_reglamento = forms.BooleanField(
        label=(
            "Acepto el reglamento del Festival de la Leyenda Vallenata y "
            "certifico que mis datos son verídicos."
        ),
        error_messages={"required": "Debes aceptar el reglamento para registrarte."},
    )

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].help_text = "Letras, números y @ . + - _"
        self.fields["password1"].help_text = "Mínimo 8 caracteres, no solo números."
        self.fields["password2"].label = "Confirmar contraseña"
        self.fields["password2"].help_text = ""
        marcadores = {
            "first_name": "Ej. Consuelo",
            "last_name": "Ej. Araujo",
            "username": "Ej. juglar27",
            "email": "tu.correo@ejemplo.com",
            "password1": "Mínimo 8 caracteres",
            "password2": "Repite tu contraseña",
        }
        for nombre, texto in marcadores.items():
            self.fields[nombre].widget.attrs["placeholder"] = texto

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este correo.")
        return email


class InicioSesionForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs["placeholder"] = "Ej. juglar27"
        self.fields["password"].widget.attrs["placeholder"] = "Tu contraseña"
