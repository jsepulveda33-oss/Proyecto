

from django.db.models import Count
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import Categoria, Edicion, Opcion, Votacion


# ---------------------------------------------------------------------------
# Funciones de apoyo
# ---------------------------------------------------------------------------
def calcular_estado(votacion):
    """
    Devuelve (clave, texto) con el estado de una votación:
      - Inactiva: el administrador la desactivó (campo 'activa' = False).
      - Próxima:  todavía no llega la fecha de inicio.
      - Cerrada:  ya pasó la fecha de fin.
      - Activa:   está dentro de su ventana de tiempo (regla RN-03).
    """
    if not votacion.activa:
        return "inactiva", "Inactiva"
    ahora = timezone.now()
    if ahora < votacion.fecha_inicio:
        return "proxima", "Próxima"
    if ahora > votacion.fecha_fin:
        return "cerrada", "Cerrada"
    return "activa", "Activa"


def _preparar_categorias(categorias):
    """
    Agrega a cada categoría cuántas votaciones tiene y un resumen de su estado.
    Usa prefetch_related para traer todas las votaciones en una sola consulta.
    """
    lista = list(categorias.prefetch_related("votaciones"))
    for c in lista:
        estados = [calcular_estado(v)[0] for v in c.votaciones.all()]
        c.total_votaciones = len(estados)
        activas = estados.count("activa")
        if activas:
            c.estado_clave = "activa"
            c.estado_texto = f"{activas} activa" + ("s" if activas > 1 else "")
        elif "proxima" in estados:
            c.estado_clave, c.estado_texto = "proxima", "Próxima"
        elif "cerrada" in estados:
            c.estado_clave, c.estado_texto = "cerrada", "Cerrada"
        elif estados:
            c.estado_clave, c.estado_texto = "inactiva", "Inactiva"
        else:
            c.estado_clave, c.estado_texto = "vacia", "Sin votaciones"
    return lista


# ---------------------------------------------------------------------------
# Vistas (una por página)
# ---------------------------------------------------------------------------
def inicio(request):
    """Página de inicio del Festival."""
    # Edición a destacar: la más reciente que esté marcada como activa.
    edicion = Edicion.objects.filter(activa=True).first() or Edicion.objects.first()
    categorias = _preparar_categorias(edicion.categorias.all()) if edicion else []
    contexto = {
        "edicion": edicion,
        "categorias": categorias,
        "total_ediciones": Edicion.objects.count(),
        "total_categorias": Categoria.objects.count(),
        "total_votaciones": Votacion.objects.count(),
        "total_opciones": Opcion.objects.count(),
    }
    return render(request, "votaciones/inicio.html", contexto)


def lista_ediciones(request):
    """Ediciones disponibles del Festival."""
    ediciones = Edicion.objects.annotate(total_categorias=Count("categorias"))
    return render(request, "votaciones/ediciones.html", {"ediciones": ediciones})


def detalle_edicion(request, edicion_id):
    """Categorías de una edición."""
    edicion = get_object_or_404(Edicion, pk=edicion_id)
    categorias = _preparar_categorias(edicion.categorias.all())
    return render(
        request,
        "votaciones/edicion_detalle.html",
        {"edicion": edicion, "categorias": categorias},
    )


def detalle_categoria(request, categoria_id):
    """Votaciones de una categoría."""
    categoria = get_object_or_404(Categoria.objects.select_related("edicion"), pk=categoria_id)
    votaciones = list(categoria.votaciones.annotate(total_opciones=Count("opciones")))
    for v in votaciones:
        v.estado_clave, v.estado_texto = calcular_estado(v)
    return render(
        request,
        "votaciones/categoria_detalle.html",
        {"categoria": categoria, "edicion": categoria.edicion, "votaciones": votaciones},
    )


def detalle_votacion(request, votacion_id):
    """Detalle de una votación y sus opciones participantes."""
    votacion = get_object_or_404(
        Votacion.objects.select_related("categoria__edicion"), pk=votacion_id
    )
    votacion.estado_clave, votacion.estado_texto = calcular_estado(votacion)
    return render(
        request,
        "votaciones/votacion_detalle.html",
        {
            "votacion": votacion,
            "categoria": votacion.categoria,
            "edicion": votacion.categoria.edicion,
            "opciones": list(votacion.opciones.all()),
        },
    )
