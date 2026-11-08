# Sistema de votaciones - Festival de la Leyenda Vallenata

Proyecto académico en **Django + MySQL** para gestionar ediciones del festival, sus categorías (concursos), votaciones y opciones, y para que los usuarios registrados voten **una sola vez por categoría**.

## Contenido

1. [Tecnologías](#tecnologías)
2. [Estructura del proyecto](#estructura-del-proyecto)
3. [Modelo de datos](#modelo-de-datos)
4. [Instalación](#instalación)
5. [Configuración de MySQL](#configuración-de-mysql)
6. [Migraciones](#migraciones)
7. [Datos de prueba](#datos-de-prueba)
8. [Cómo correr el proyecto](#cómo-correr-el-proyecto)
9. [API: `GET /api/categorias/`](#api-get-apicategorias)
10. [Pruebas](#pruebas)
11. [Solución de problemas](#solución-de-problemas)
12. [Notas de seguridad](#notas-de-seguridad)

---

## Tecnologías

| Componente | Versión |
|---|---|
| Python | 3.13 |
| Django | 6.0.x |
| MySQL Server | 8.0 o superior |
| mysqlclient | 2.3.0 |
| python-dotenv | 1.2.4 |

> **Importante:** el proyecto usa **Django 6.0** y no 6.1. Django 6.1 exige MySQL 8.4 o superior, y este proyecto se desarrolló con MySQL 8.0.46. No actualices Django sin actualizar también MySQL.

## Estructura del proyecto

```
Proyecto/
├── manage.py
├── requirements.txt          # dependencias de Python
├── .env.example              # plantilla de configuración (sin contraseña)
├── .gitignore                # evita subir .env, venv, etc.
├── config/                   # configuración general (settings.py, urls.py)
├── votaciones/               # aplicación principal
│   ├── models.py             # Edicion, Categoria, Votacion, Opcion, Voto
│   ├── views.py              # páginas, voto y API
│   ├── urls.py               # rutas de la aplicación
│   ├── forms.py              # formulario de voto
│   ├── admin.py              # modelos registrados en Django Admin
│   ├── migrations/           # migraciones de la base de datos
│   ├── fixtures/
│   │   └── datos_iniciales.json   # datos de prueba
│   └── management/commands/
│       ├── crear_usuarios_prueba.py   # crea 4 usuarios ficticios
│       └── prueba_concurrencia.py     # prueba CP-09
└── cuentas/                  # inicio de sesión de los votantes (/cuentas/)
```

## Modelo de datos

Los datos forman una cadena: una **Edición** tiene varias **Categorías** (los concursos), una Categoría tiene varias **Votaciones**, y una Votación tiene varias **Opciones** (los concursantes). Cada voto emitido se guarda en **Voto**.

```
Edicion 1 ──< Categoria 1 ──< Votacion 1 ──< Opcion
                  │
                  └──< Voto >── Usuario
```

| Modelo | Campos principales |
|---|---|
| `Edicion` | nombre, anio, fecha_inicio, fecha_fin, activa |
| `Categoria` | edicion, nombre, descripcion |
| `Votacion` | categoria, nombre, descripcion, fecha_inicio, fecha_fin, activa |
| `Opcion` | votacion, nombre, descripcion, votos |
| `Voto` | usuario, edicion, categoria, opcion, fecha_voto |

**Regla de negocio:** un usuario solo puede votar una vez por categoría y edición. Se garantiza con una restricción única en la base de datos (`voto_unico_usuario_categoria_edicion`), y el contador `Opcion.votos` se incrementa de forma atómica dentro de una transacción.

---

## Instalación

### Requisitos previos

- Python 3.13
- MySQL Server 8.0 o superior, en ejecución y escuchando en el puerto 3306
- Git (opcional si se descarga el proyecto como ZIP)

### Pasos (Windows, PowerShell)

**1. Obtener el proyecto** y abrir una terminal en la carpeta que contiene `manage.py`.

**2. Crear el entorno virtual**

```
py -3.13 -m venv venv
```

**3. Activarlo**

```
venv\Scripts\Activate.ps1
```

Debe aparecer `(venv)` al inicio de la línea de la terminal.

**4. Instalar las dependencias**

```
pip install -r requirements.txt
```

> En macOS o Linux: `python3 -m venv venv`, `source venv/bin/activate` y el mismo `pip install -r requirements.txt`.

---

## Configuración de MySQL

**1. Crear la base de datos.** Abre el cliente de MySQL (por ejemplo, *MySQL 8.0 Command Line Client*), entra con tu contraseña de `root` y ejecuta:

```sql
CREATE DATABASE votaciones CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

**2. Crear tu archivo `.env`.** Copia la plantilla y escribe tu contraseña de MySQL en `DB_PASSWORD`:

```
copy .env.example .env
```

(en macOS o Linux: `cp .env.example .env`)

Contenido del archivo:

```
DB_NAME=votaciones
DB_USER=root
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=3306
```

El archivo `.env` es **personal** y está en `.gitignore`: nunca se sube al repositorio.

**3. Verificar la conexión** (con el entorno activo):

```
python manage.py shell -c "from django.db import connection; c = connection.cursor(); c.execute('SELECT VERSION(), DATABASE()'); print(c.fetchone())"
```

Resultado esperado, con la versión de tu servidor:

```
('8.0.46', 'votaciones')
```

---

## Migraciones

Crean las tablas del sistema en MySQL:

```
python manage.py migrate
```

Si se modifican los modelos, primero se generan con `python manage.py makemigrations`. Para comprobar que no quedan cambios sin migrar: `python manage.py makemigrations --check --dry-run`.

---

## Datos de prueba

**1. Ediciones, categorías, votaciones y opciones** (archivo de datos):

```
python manage.py loaddata datos_iniciales
```

Carga 46 objetos: 1 edición ("Festival de la Leyenda Vallenata", 2026), 9 categorías, 9 votaciones y 27 opciones.

| Categoría (concurso) |
|---|
| Canción Vallenata Inédita |
| Acordeón Profesional |
| Acordeón Aficionado |
| Piquería Mayor |
| Acordeonera Mayor |
| Acordeonera Menor |
| Acordeón Juvenil |
| Acordeón Infantil |
| Piquería Infantil |

Cada votación tiene tres opciones de relleno (`Concursante 1`, `2` y `3`). Los nombres de los concursantes son ficticios.

> Las votaciones de prueba están activas del **1 al 30 de noviembre de 2026**. Pasada esa fecha aparecerán como cerradas y la prueba de concurrencia no encontrará una votación activa. Para extenderlas, edita las fechas desde el panel de administración.

**2. Usuarios ficticios para votar** (4 usuarios):

```
python manage.py crear_usuarios_prueba
```

| Usuario | Contraseña |
|---|---|
| `votante1` a `votante4` | `Prueba12345` |

Son usuarios de **prueba para desarrollo local**. El correo de cada uno es `<usuario>@example.com`.

**3. Usuario administrador** (para entrar a `/admin/`):

```
python manage.py createsuperuser
```

---

## Cómo correr el proyecto

Con el entorno virtual activo:

```
python manage.py runserver
```

El servidor queda en http://127.0.0.1:8000/. Usa siempre `127.0.0.1` y no `localhost`, para que las cookies de sesión no se mezclen.

| Dirección | Descripción |
|---|---|
| `/` | Página de inicio del festival |
| `/ediciones/` | Ediciones disponibles |
| `/ediciones/<id>/` | Categorías de una edición |
| `/categorias/<id>/` | Votaciones de una categoría |
| `/votaciones/<id>/` | Detalle de una votación y sus opciones |
| `/categorias/<id>/votar/` | Registra un voto (POST, requiere iniciar sesión) |
| `/cuentas/iniciar-sesion/` | Inicio de sesión de los votantes |
| `/admin/` | Panel de administración de Django |
| `/api/categorias/` | API JSON de categorías y opciones |

Para votar: inicia sesión con un usuario de prueba, entra a una categoría, elige su votación y selecciona una opción. Un segundo intento en la misma categoría se rechaza.

---

## API: `GET /api/categorias/`

Devuelve en formato JSON todas las categorías con su edición y sus opciones, leídas desde MySQL. Solo acepta el método `GET`.

```
http://127.0.0.1:8000/api/categorias/
```

Ejemplo de respuesta (recortada):

```json
{
  "categorias": [
    {
      "id": 3,
      "nombre": "Acordeón Aficionado",
      "descripcion": "Concurso de Acordeón Aficionado.",
      "edicion": {
        "id": 1,
        "nombre": "Festival de la Leyenda Vallenata",
        "anio": 2026
      },
      "opciones": [
        {
          "id": 7,
          "nombre": "Concursante 1",
          "descripcion": "",
          "votos": 0,
          "votacion_id": 3
        }
      ]
    }
  ]
}
```

Las opciones se devuelven agrupadas bajo su categoría. El campo `votacion_id` indica a qué votación pertenece cada una.

---

## Pruebas

### CP-09: solicitudes de voto simultáneas

Comprueba que el sistema no pierde votos ni permite votos duplicados cuando llegan dos solicitudes al mismo tiempo. Usa la base de datos MySQL real y **no necesita el servidor encendido**.

Requisitos: haber ejecutado `migrate`, `loaddata datos_iniciales` y `crear_usuarios_prueba`, y que exista una votación activa.

```
python manage.py prueba_concurrencia
```

| Escenario | Qué se hace | Resultado esperado |
|---|---|---|
| A | El **mismo usuario** envía 2 votos a la vez | 1 voto guardado. Una solicitud registra el voto y la otra recibe "Ya votaste en esta categoría" |
| B | **Dos usuarios distintos** votan por la misma opción a la vez | 2 votos guardados y el contador de la opción sube 2 |

Al final debe aparecer `CP-09 COMPLETO: PASA`. El comando elimina los votos de prueba y restaura los contadores. Con la opción `--conservar` los deja para poder revisarlos en MySQL.

**Nota técnica:** en la vista `votar`, dentro de `transaction.atomic()`, primero se actualiza el contador de la opción con `F("votos") + 1` y después se crea el `Voto`. Con el orden contrario, dos votos simultáneos por la misma opción provocaban un bloqueo mutuo en MySQL (error 1213, *deadlock*). Si el usuario ya votó, la restricción única genera `IntegrityError` y la transacción completa se revierte.

### Pruebas manuales

| # | Prueba | Cómo | Resultado esperado |
|---|---|---|---|
| 1 | Conexión con MySQL | Comando de la sección *Configuración de MySQL* | `('8.0.xx', 'votaciones')` |
| 2 | Tablas y datos | En MySQL: `USE votaciones;` y `SHOW TABLES;` | Aparecen `votaciones_edicion`, `_categoria`, `_votacion`, `_opcion` y `_voto` |
| 3 | Usuarios | En MySQL: `SELECT username, is_superuser FROM auth_user;` | `votante1` a `votante4` y el administrador |
| 4 | API | Abrir `/api/categorias/` | JSON con 9 categorías y sus opciones |
| 5 | Votar | Iniciar sesión con `votante3`, votar y repetir el voto | "Voto registrado" y luego se rechaza el segundo; `votos` sube 1 en la API |

---

## Solución de problemas

| Problema | Causa y solución |
|---|---|
| PowerShell: "la ejecución de scripts está deshabilitada" | Ejecutar una vez `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` y volver a activar el entorno |
| `NotSupportedError: MySQL 8.4 or later is required` | Se instaló Django 6.1 con MySQL 8.0. Usar Django 6.0 (`pip install "django<6.1"`) o actualizar MySQL a 8.4 |
| Falla `pip install mysqlclient` | Verificar que se usa Python 3.13 y que el entorno virtual está activo |
| `mysql` no se reconoce en la terminal | El cliente no está en el PATH de Windows. Usar *MySQL 8.0 Command Line Client* desde el menú de inicio |
| `Access denied for user 'root'` | La contraseña de `DB_PASSWORD` en `.env` no coincide con la de MySQL |
| `Unknown database 'votaciones'` | Falta crear la base de datos (sección *Configuración de MySQL*) |
| Error 403 (CSRF) al iniciar sesión | Cookies viejas del navegador. Probar en una ventana de incógnito, usar `127.0.0.1` y recargar con Ctrl + F5 antes de enviar el formulario |
| `AttributeError: module 'votaciones.views' has no attribute ...` | El archivo no estaba guardado o falta bajar cambios del repositorio. Guardar con Ctrl + S y reiniciar el servidor |
| "You have unapplied migration(s)" | Ejecutar `python manage.py migrate` |
| La prueba CP-09 dice que no hay votación activa | Las fechas de los datos de prueba ya vencieron. Ajustarlas desde `/admin/` |

---

## Notas de seguridad

- El archivo `.env` contiene la contraseña de MySQL y **no debe subirse** al repositorio. Está en `.gitignore`; se comparte solo `.env.example`.
- `settings.py` conserva la `SECRET_KEY` de desarrollo que genera Django (`django-insecure-...`) y `DEBUG = True`. Son adecuados para trabajo local y académico. Antes de publicar el sitio de verdad, hay que cambiar la clave, moverla a variables de entorno y desactivar `DEBUG`.
- Las contraseñas de los usuarios de prueba son ficticias y solo sirven para desarrollo local.
