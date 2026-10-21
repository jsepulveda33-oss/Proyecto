from django.db import models


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
    