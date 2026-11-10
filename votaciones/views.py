
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Count, F
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import VotoForm
from .models import Categoria, Edicion, Opcion, Voto, Votacion


# ---------------------------------------------------------------------------
# Funciones de apoyo
# ---------------------------------------------------------------------------
def calcular_estado(votacion):

   
    if not votacion.activa:
        return "inactiva", "Inactiva"
    ahora = timezone.now()
    if ahora < votacion.fecha_inicio:
        return "proxima", "Próxima"
    if ahora > votacion.fecha_fin:
        return "cerrada", "Cerrada"
    return "activa", "Activa"


def _preparar_categorias(categorias):

 
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
    voto_previo = None
    if request.user.is_authenticated:
        voto_previo = (
            Voto.objects.filter(
                usuario=request.user,
                categoria=votacion.categoria,
                edicion=votacion.categoria.edicion,
            )
            .select_related("opcion")
            .first()
        )
    return render(
        request,
        "votaciones/votacion_detalle.html",
        {
            "voto_previo": voto_previo,
            "votacion": votacion,
            "categoria": votacion.categoria,
            "edicion": votacion.categoria.edicion,
            "opciones": list(votacion.opciones.all()),
        },
    )


# ---------------------------------------------------------------------------
# Núcleo del voto (Compañero 1)
# ---------------------------------------------------------------------------
@login_required
def votar(request, categoria_id):

    
    categoria = get_object_or_404(Categoria.objects.select_related("edicion"), pk=categoria_id)

    if request.method != "POST":
        # Evita el 405 al volver del login: se muestra la categoría.
        return redirect("categoria_detalle", categoria_id=categoria.pk)

    # Página a la que se regresa (la votación desde la que se votó, si es de esta categoría).
    destino = redirect("categoria_detalle", categoria_id=categoria.pk)
    votacion_id = request.POST.get("votacion", "")
    if votacion_id.isdigit() and categoria.votaciones.filter(pk=votacion_id).exists():
        destino = redirect("votacion_detalle", votacion_id=int(votacion_id))

    form = VotoForm(request.POST, categoria=categoria, usuario=request.user)
    if not form.is_valid():
        for errores in form.errors.values():
            for error in errores:
                messages.error(request, error)
        return destino

    opcion = form.cleaned_data["opcion"]
    try:
        with transaction.atomic():
            # 1) Primero se bloquea y se actualiza la fila de la opción.
            Opcion.objects.filter(pk=opcion.pk).update(votos=F("votos") + 1)
            # 2) Después se crea el voto. Si el usuario ya votó, salta
            #    IntegrityError y todo se revierte, incluido el contador.
            Voto.objects.create(
                usuario=request.user,
                edicion=categoria.edicion,
                categoria=categoria,
                opcion=opcion,
            )
    except IntegrityError:
        messages.error(request, "Ya votaste en esta categoría.")
    else:
        messages.success(request, f"¡Voto registrado para «{opcion.nombre}»!")
    return destino

@login_required
def mis_votos(request):
    """CP-07: categorías en las que el usuario autenticado ya votó."""
    votos = (
        Voto.objects.filter(usuario=request.user)
        .select_related("edicion", "categoria", "opcion__votacion")
    )
    return render(request, "votaciones/mis_votos.html", {"votos": votos})


@require_GET
def api_categorias(request):
    """GET /api/categorias/ -> categorías con sus opciones, leídas desde MySQL."""
    categorias = (
        Categoria.objects
        .select_related("edicion")
        .prefetch_related("votaciones__opciones")
    )
    data = []
    for c in categorias:
        opciones = []
        for v in c.votaciones.all():
            for o in v.opciones.all():
                opciones.append({
                    "id": o.id,
                    "nombre": o.nombre,
                    "descripcion": o.descripcion,
                    "votos": o.votos,
                    "votacion_id": v.id,
                })
        data.append({
            "id": c.id,
            "nombre": c.nombre,
            "descripcion": c.descripcion,
            "edicion": {
                "id": c.edicion_id,
                "nombre": c.edicion.nombre,
                "anio": c.edicion.anio,
            },
            "opciones": opciones,
        })
    return JsonResponse(
        {"categorias": data},
        json_dumps_params={"ensure_ascii": False},
    ) 
