from django.contrib import admin

from .models import Categoria, Edicion, Opcion, Votacion


@admin.register(Edicion)
class EdicionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "anio", "fecha_inicio", "fecha_fin", "activa")
    list_filter = ("activa", "anio")
    search_fields = ("nombre",)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "edicion")
    list_filter = ("edicion",)
    search_fields = ("nombre",)


class OpcionInline(admin.TabularInline):
    model = Opcion
    extra = 2


@admin.register(Votacion)
class VotacionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "categoria", "fecha_inicio", "fecha_fin", "activa")
    list_filter = ("activa", "categoria__edicion")
    search_fields = ("nombre",)
    inlines = [OpcionInline]


@admin.register(Opcion)
class OpcionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "votacion", "votos")
    list_filter = ("votacion",)
    search_fields = ("nombre",)
    