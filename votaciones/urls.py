
from django.urls import path

from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("api/categorias/", views.api_categorias, name="api_categorias"),
    path("ediciones/", views.lista_ediciones, name="ediciones"),
    path("ediciones/<int:edicion_id>/", views.detalle_edicion, name="edicion_detalle"),
    path("categorias/<int:categoria_id>/", views.detalle_categoria, name="categoria_detalle"),
    path("votaciones/<int:votacion_id>/", views.detalle_votacion, name="votacion_detalle"),
    path("categorias/<int:categoria_id>/votar/", views.votar, name="votar"),

]
