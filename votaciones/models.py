from django.db import models
from django.conf import settings

class Edicion(models.Model):
    nombre = models.CharField(max_length=100)
    anio = models.PositiveIntegerField("año")
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Edición"
        verbose_name_plural = "Ediciones"
        ordering = ["-anio"]

    def __str__(self):
        return f"{self.nombre} ({self.anio})"


class Categoria(models.Model):
    edicion = models.ForeignKey(
        Edicion, on_delete=models.CASCADE, related_name="categorias"
    )
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} - {self.edicion}"


class Votacion(models.Model):
    categoria = models.ForeignKey(
        Categoria, on_delete=models.CASCADE, related_name="votaciones"
    )
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Votación"
        verbose_name_plural = "Votaciones"
        ordering = ["-fecha_inicio"]

    def __str__(self):
        return self.nombre


class Opcion(models.Model):
    votacion = models.ForeignKey(
        Votacion, on_delete=models.CASCADE, related_name="opciones"
    )
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    votos = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Opción"
        verbose_name_plural = "Opciones"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.votacion})"

class Voto(models.Model):
    """Un voto de un usuario por categoría y edición (RN: un solo voto)."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="votos"
    )
    edicion = models.ForeignKey(Edicion, on_delete=models.PROTECT, related_name="votos")
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="votos")
    opcion = models.ForeignKey(Opcion, on_delete=models.PROTECT, related_name="registros_voto")
    fecha_voto = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_voto"]
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "categoria", "edicion"],
                name="voto_unico_usuario_categoria_edicion",
            )
        ]

    def __str__(self):
        return f"{self.usuario} → {self.opcion} ({self.categoria})"
 