# Sistema de votaciones - Festival Vallenato

Proyecto Django + MySQL para gestionar ediciones, categorías (concursos), votaciones y opciones.

## Requisitos

- Python 3.13
- MySQL Server 8.0 o superior, funcionando en el puerto 3306
- Visual Studio Code (recomendado)

## Instalación paso a paso

**1. Abrir una terminal en la carpeta del proyecto** (la que contiene `manage.py`).

**2. Crear el entorno virtual**

```
py -3.13 -m venv venv
```

(En macOS o Linux: `python3 -m venv venv`)

**3. Activar el entorno virtual**

- Windows PowerShell: `venv\Scripts\Activate.ps1`
- Windows cmd: `venv\Scripts\activate.bat`
- macOS / Linux: `source venv/bin/activate`

Debe aparecer `(venv)` al inicio de la línea de la terminal.

**4. Instalar las dependencias**

```
pip install -r requirements.txt
```

**5. Crear la base de datos en MySQL**

Abre el cliente de MySQL (por ejemplo, MySQL 8.0 Command Line Client), entra con tu contraseña de root y ejecuta:

```
CREATE DATABASE votaciones CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

**6. Crear tu archivo de configuración `.env`**

Copia `.env.example` con el nombre `.env` y escribe tu contraseña de MySQL en `DB_PASSWORD`:

```
copy .env.example .env
```

(En macOS o Linux: `cp .env.example .env`)

El archivo `.env` es personal y no se sube al repositorio.

**7. Crear las tablas**

```
python manage.py migrate
```

**8. Cargar los datos de prueba**

```
python manage.py loaddata datos_iniciales
```

**9. Crear un usuario administrador**

```
python manage.py createsuperuser
```

**10. Encender el servidor**

```
python manage.py runserver
```

Abre http://127.0.0.1:8000/admin/ e inicia sesión con el usuario del paso 9.

## Estructura

- `config/`: configuración general del proyecto (`settings.py`, `urls.py`)
- `votaciones/models.py`: modelos Edicion, Categoria, Votacion y Opcion
- `votaciones/admin.py`: registro de los modelos en Django Admin
- `votaciones/fixtures/datos_iniciales.json`: datos de prueba
- `requirements.txt`: dependencias de Python

## Problemas frecuentes

- **PowerShell dice que la ejecución de scripts está deshabilitada:** ejecuta una vez `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`.
- **`pip install` falla al instalar `mysqlclient`:** verifica que usas Python 3.13 y avisa al equipo.
- **Error "MySQL 8.4 or later is required":** Django 6.1 exige MySQL 8.4 o superior. Este proyecto usa Django 6.0, que funciona con MySQL 8.0. No actualices Django sin actualizar MySQL.