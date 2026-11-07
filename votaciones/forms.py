"""
Formulario de voto (Núcleo del voto).
Concentra TODAS las validaciones de negocio antes de escribir en la BD.
"""
from django import forms
from django.utils import timezone

from .models import Opcion, Voto


class VotoForm(forms.Form):
    opcion = forms.ModelChoiceField(
        queryset=Opcion.objects.none(),
        error_messages={
            "required": "Debes seleccionar una opción.",
            "invalid_choice": "La opción no pertenece a esta categoría.",
        },
    )

    def __init__(self, *args, categoria, usuario, **kwargs):
        super().__init__(*args, **kwargs)
        self.categoria = categoria
        self.usuario = usuario
        # Solo son válidas las opciones de las votaciones de ESTA categoría (CP-06).
        self.fields["opcion"].queryset = Opcion.objects.filter(
            votacion__categoria=categoria
        ).select_related("votacion")

    def clean_opcion(self):
        opcion = self.cleaned_data["opcion"]
        votacion = opcion.votacion
        edicion = self.categoria.edicion

        # Votación habilitada (CP-05): activa y dentro de su ventana de tiempo.
        ahora = timezone.now()
        if not (
            votacion.activa
            and edicion.activa
            and votacion.fecha_inicio <= ahora <= votacion.fecha_fin
        ):
            raise forms.ValidationError("Esta votación no está habilitada.")
        return opcion

    def clean(self):
        cleaned = super().clean()
        # Sin voto previo del usuario en la categoría y edición (CP-03).
        if Voto.objects.filter(
            usuario=self.usuario,
            categoria=self.categoria,
            edicion=self.categoria.edicion,
        ).exists():
            raise forms.ValidationError("Ya votaste en esta categoría.")
        return cleaned
