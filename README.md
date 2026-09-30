# Intranet · Centro Médico Santa Rosa de Lima — API REST
 
API de ejemplo de la **intranet de gestión** de un centro médico, desarrollada con **FastAPI** para el
**Proyecto Intermodular del CFGS Desarrollo de Aplicaciones Web (DAW)**.

Es un escenario **equivalente** al de la intranet del centro educativo: cambia el contexto (un centro médico),
pero se mantienen los mismos patrones. Sirve como referencia de cómo definir, documentar, implementar y probar
los endpoints de vuestro propio backend.

| Proyecto del centro educativo | Este ejemplo (centro médico) |
|---|---|
| Guardias del profesorado por rondas | Guardias médicas por rondas |
| Ausencias del profesorado con PDF y firma | Ausencias del personal con PDF y firma |
| Tickets: RMI, compras, RRSS | Tickets: mantenimiento, suministros, RRSS |
| Reserva de espacios y recursos | Reserva de salas y equipos |
| Tablón por departamento | Tablón por servicio |
| Dashboard del equipo directivo | Dashboard de dirección |

> ⚠️ **Proyecto didáctico.** Los datos se guardan **en memoria** (se reinician al parar el servidor) y algunas
> integraciones están **simuladas** (ver [Limitaciones](#12-limitaciones-qué-está-simulado)).

---

## Índice

1. [Tecnologías](#1-tecnologías)
2. [Estructura del proyecto](#2-estructura-del-proyecto)
3. [Requisitos previos](#3-requisitos-previos)
4. [Instalación y ejecución en local](#4-instalación-y-ejecución-en-local)
5. [Probar la API desde el navegador (Swagger UI)](#5-probar-la-api-desde-el-navegador-swagger-ui)
6. [Usuarios de ejemplo](#6-usuarios-de-ejemplo)
7. [Endpoints](#7-endpoints)
8. [Reglas de negocio implementadas](#8-reglas-de-negocio-implementadas)
9. [Pruebas automatizadas (pytest)](#9-pruebas-automatizadas-pytest)
10. [Ejecución con Docker (opcional)](#10-ejecución-con-docker-opcional)
11. [Contrato OpenAPI y editor.swagger.io](#11-contrato-openapi-y-editorswaggerio)
12. [Limitaciones: qué está simulado](#12-limitaciones-qué-está-simulado)
13. [Publicar el proyecto en GitHub o GitLab](#13-publicar-el-proyecto-en-github-o-gitlab)
14. [Documentación pública en GitHub Pages (Swagger)](#14-documentación-pública-en-github-pages-swagger)
15. [Licencia](#15-licencia)

---

## 1. Tecnologías

- **Python 3.10 o superior**
- **FastAPI**: framework de la API REST y documentación automática (OpenAPI).
- **Uvicorn**: servidor ASGI para ejecutar la aplicación.
- **PyJWT**: tokens JWT de acceso (*access*) y renovación (*refresh*).
- **Pydantic**: validación de los datos de entrada y salida.
- **pytest**: pruebas automatizadas.
- **Docker** (opcional): contenerización.

## 2. Estructura del proyecto

```
intranet-santa-rosa-api/
├── app/
│   ├── main.py            # Punto de entrada: crea la app y registra los routers
│   ├── config.py          # Configuración leída del fichero .env
│   ├── db.py              # Datos de ejemplo EN MEMORIA, auditoría y notificaciones
│   ├── security.py        # JWT y control de roles mediante Depends()
│   ├── schemas.py         # Modelos Pydantic (peticiones y respuestas)
│   ├── routers/           # Un fichero por recurso de la API
│   │   ├── auth.py        # /auth
│   │   ├── usuarios.py    # /usuarios
│   │   ├── anuncios.py    # /anuncios
│   │   ├── guardias.py    # /guardias
│   │   ├── ausencias.py   # /ausencias
│   │   ├── tickets.py     # /tickets
│   │   ├── reservas.py    # /reservas
│   │   └── direccion.py   # /dashboard y /auditoria
│   └── services/
│       ├── guardias.py    # Algoritmo de asignación por rondas
│       └── pdf.py         # Generador de PDF mínimo
├── tests/                 # Pruebas automatizadas con pytest
├── docs/
│   └── openapi-intranet-santa-rosa.yaml   # Contrato OpenAPI 3.0.3
├── scripts/
│   └── export_openapi.py  # Genera la documentación estática desde el código
├── site/
│   └── index.html         # Página Swagger UI que se publica en GitHub Pages
├── .github/workflows/
│   └── pages.yml          # CI/CD: tests + publicación en GitHub Pages
├── .gitlab-ci.yml         # Equivalente para GitLab Pages
├── .env.example           # Plantilla de variables de entorno
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
└── LICENSE
```

## 3. Requisitos previos

- **Python 3.10 o superior.** Comprueba la versión con:
  ```bash
  python --version      # En Linux/macOS puede ser: python3 --version
  ```
- **Git**, para clonar el repositorio o subirlo.
- *(Opcional)* **Docker Desktop**, si quieres ejecutarlo en un contenedor.

## 4. Instalación y ejecución en local

### 4.1. Obtener el código

Descomprime el ZIP o clona el repositorio y entra en la carpeta:

```bash
cd intranet-santa-rosa-api
```

### 4.2. Crear y activar un entorno virtual

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```
> Si PowerShell bloquea el script, ejecuta una vez:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y vuelve a activarlo.
> En **CMD** se activa con `.venv\Scripts\activate.bat`.

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Sabrás que está activo porque la línea de comandos empieza por `(.venv)`.

### 4.3. Instalar las dependencias

```bash
pip install -r requirements.txt
```

### 4.4. Configurar las variables de entorno

Copia la plantilla y, si quieres, cambia la clave secreta:

```bash
# Windows (PowerShell)
Copy-Item .env.example .env
# Linux / macOS
cp .env.example .env
```

| Variable | Descripción | Valor por defecto |
|---|---|---|
| `SECRET_KEY` | Clave para firmar los JWT. **Cámbiala** en cualquier despliegue | valor de ejemplo |
| `ACCESS_TOKEN_MINUTES` | Duración del *access token* | `30` |
| `REFRESH_TOKEN_DAYS` | Duración del *refresh token* | `7` |
| `DEMO_MODE` | `true`: el login acepta el email en lugar del token real de Google | `true` |

> El fichero `.env` **nunca se sube al repositorio** (ya está incluido en `.gitignore`).
> Si no creas el `.env`, se usan los valores por defecto.

### 4.5. Arrancar el servidor

```bash
uvicorn app.main:app --reload
```

Verás un mensaje parecido a `Uvicorn running on http://127.0.0.1:8000`. La opción `--reload` reinicia el
servidor automáticamente al guardar cambios en el código.

| Dirección | Contenido |
|---|---|
| http://127.0.0.1:8000/docs | Documentación interactiva **Swagger UI** |
| http://127.0.0.1:8000/redoc | Documentación en formato **ReDoc** |
| http://127.0.0.1:8000/openapi.json | Contrato OpenAPI generado por FastAPI |

> **En el aula**, para que otros equipos de la red accedan al servidor:
> `uvicorn app.main:app --host 0.0.0.0 --port 8000` y usa la IP del equipo (por ejemplo, `http://192.168.1.20:8000/docs`).

Para detener el servidor, pulsa `Ctrl + C`.

## 5. Probar la API desde el navegador (Swagger UI)

1. Abre http://127.0.0.1:8000/docs.
2. Despliega **`POST /api/v1/auth/google`** → **Try it out**.
3. En el cuerpo escribe el email de un usuario de ejemplo y pulsa **Execute**:
   ```json
   { "id_token": "laura.martinez@santarosadelima.es" }
   ```
4. Copia el valor de `access_token` de la respuesta.
5. Pulsa el botón **Authorize** 🔓 (arriba a la derecha), pega el token y pulsa **Authorize**.
6. Ya puedes probar el resto de endpoints. Para probar con otro rol, repite el login con otro usuario.

### Recorrido sugerido para clase

| Paso | Usuario | Endpoint | Qué se observa |
|---|---|---|---|
| 1 | Elena (pendiente) | `POST /auth/google` | 403: pendiente de confirmación |
| 2 | Laura (admin) | `PATCH /usuarios/u9` con `{"estado": "activo"}` | Aprobación del alta |
| 3 | Carlos (supervisión) | `POST /guardias/asignar` con `{"fecha": "2026-10-05", "franja": "noche"}` | Se asigna a **Ana** (menos guardias) |
| 4 | Carlos | `PATCH /guardias/{id}` con `{"realizada_por": "u4"}` | Javier la cubre y su contador sube |
| 5 | Ana | `POST /ausencias` con tipo `generica` | Estado `pendiente_justificante` |
| 6 | Ana | `POST /ausencias/{id}/justificante` → `GET /ausencias/{id}/pdf` → `POST /ausencias/{id}/firma` | Flujo completo con PDF real |
| 7 | Ana | `POST /reservas` dos veces en la misma franja | La segunda devuelve **409** |
| 8 | Pedro (mantenimiento) | `PATCH /tickets/t1` con `{"estado": "finalizado"}` | **409**: hay que pasar antes por `en_curso` |
| 9 | Laura (dirección) | `GET /dashboard/kpis` y `GET /auditoria` | Indicadores y registro de acciones |

### Ejemplos con curl (Linux, macOS o Git Bash)

```bash
# 1. Login y guardar el token
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/google \
  -H "Content-Type: application/json" \
  -d '{"id_token": "carlos.ruiz@santarosadelima.es"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 2. Asignar la guardia del lunes 5 de octubre por la noche (2 plazas)
curl -s -X POST http://127.0.0.1:8000/api/v1/guardias/asignar \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"fecha": "2026-10-05", "franja": "noche", "plazas": 2}'
```

## 6. Usuarios de ejemplo

En modo demostración, el login se hace escribiendo el **email** en el campo `id_token`.

| Id | Nombre | Email | Servicio | Roles | Estado |
|---|---|---|---|---|---|
| u1 | Laura Martínez | laura.martinez@santarosadelima.es | Dirección | personal, **admin**, **direccion** | activo |
| u2 | Carlos Ruiz | carlos.ruiz@santarosadelima.es | Supervisión | personal, **supervision** | activo |
| u3 | Ana García | ana.garcia@santarosadelima.es | Urgencias | personal | activo |
| u4 | Javier López | javier.lopez@santarosadelima.es | Urgencias | personal | activo |
| u5 | Marta Sánchez | marta.sanchez@santarosadelima.es | Pediatría | personal | activo |
| u6 | Pedro Gómez | pedro.gomez@santarosadelima.es | Mantenimiento | personal, **mantenimiento** | activo |
| u7 | Lucía Fernández | lucia.fernandez@santarosadelima.es | Administración | personal, **suministros** | activo |
| u8 | Sergio Navarro | sergio.navarro@santarosadelima.es | Comunicación | personal, **rrss** | activo |
| u9 | Elena Torres | elena.torres@santarosadelima.es | Pediatría | personal | **pendiente** |

- Si usas un email que no existe, se crea un usuario en estado **pendiente** que debe aprobar un administrador.
- Ana, Javier y Marta están disponibles para las **guardias de noche** de todos los días, con 3, 5 y 4 guardias
  realizadas respectivamente, igual que en el ejemplo de la memoria técnica.
- Recursos reservables: `sala-reuniones-1`, `aula-formacion`, `ecografo-portatil` y `proyector-1`.

## 7. Endpoints

Todas las rutas empiezan por **`/api/v1`**. *Auth* = requiere token; entre paréntesis, el rol necesario.

| Método | Ruta | Descripción | Acceso |
|---|---|---|---|
| POST | `/auth/google` | Login con Google (OAuth) → tokens JWT | Público |
| POST | `/auth/refresh` | Renovar el access token | Público (refresh token) |
| GET | `/auth/me` | Datos del usuario autenticado | Auth |
| GET | `/usuarios` | Listar usuarios (filtro `?estado=`) | Auth (admin) |
| PATCH | `/usuarios/{usuario_id}` | Modificar parcialmente (p. ej. aprobar alta) | Auth (admin) |
| PUT | `/usuarios/{usuario_id}/roles` | Sustituir la lista de roles | Auth (admin) |
| GET | `/anuncios` | Tablón: generales + del servicio, sin caducados | Auth |
| POST | `/anuncios` | Publicar anuncio | Auth (direccion, supervision) |
| GET | `/guardias` | Consultar guardias (`?fecha=&franja=`) | Auth |
| POST | `/guardias/asignar` | Asignación por rondas | Auth (supervision) |
| PATCH | `/guardias/{guardia_id}` | Registrar quién realiza la guardia | Auth (supervision) |
| POST | `/ausencias` | Registrar ausencia | Auth |
| POST | `/ausencias/{ausencia_id}/justificante` | Adjuntar justificante (multipart) | Auth (titular) |
| GET | `/ausencias/{ausencia_id}/pdf` | Descargar el documento PDF | Auth (titular) |
| POST | `/ausencias/{ausencia_id}/firma` | Firmar (manuscrita o AutoFirma) | Auth (titular) |
| GET | `/tickets` | Listar tickets (`?tipo=&estado=`) | Auth |
| POST | `/tickets` | Crear ticket (mantenimiento, suministros, rrss) | Auth |
| PATCH | `/tickets/{ticket_id}` | Cambiar el estado | Auth (responsable del tipo) |
| GET | `/reservas` | Consultar reservas (`?recurso_id=&fecha=`) | Auth |
| POST | `/reservas` | Reservar sala o equipo (409 si solapa) | Auth |
| GET | `/dashboard/kpis` | Indicadores de dirección | Auth (direccion) |
| GET | `/auditoria` | Registro de auditoría | Auth (direccion) |

### ¿POST, PUT o PATCH?

| Método | Cuándo usarlo | Ejemplo en esta API |
|---|---|---|
| **POST** | Crear un recurso nuevo o lanzar una **acción/proceso** no idempotente | `POST /tickets`, `POST /guardias/asignar` |
| **PUT** | **Sustituir por completo** un recurso: se envía la representación entera | `PUT /usuarios/{id}/roles` (lista completa de roles) |
| **PATCH** | **Modificar parcialmente** un recurso: solo se envían los campos que cambian | `PATCH /tickets/{id}` con `{"estado": "en_curso"}` |

*Idempotente* significa que repetir la misma petición deja el sistema igual que hacerla una vez. PUT lo es;
POST normalmente no (cada llamada crea algo nuevo).

### Códigos de respuesta utilizados

| Código | Significado |
|---|---|
| 200 | Correcto |
| 201 | Recurso creado |
| 401 | Falta el token o no es válido |
| 403 | El usuario no tiene permiso (rol) o está pendiente |
| 404 | El recurso no existe |
| 409 | Conflicto: duplicado, solapamiento o transición de estado no válida |
| 422 | Datos de entrada no válidos |
| 501 | Funcionalidad no disponible (AutoFirma en la demo) |

## 8. Reglas de negocio implementadas

### Guardias por rondas (`app/services/guardias.py`)
1. Cada **hueco** es día de la semana + franja (`lunes-noche`). Puede tener varias plazas.
2. Se guarda un **contador de guardias realizadas** por profesional y hueco.
3. Se asigna a quien tiene el **contador más bajo** entre los **disponibles en ese hueco** (no entre toda la plantilla).
   Los profesionales con una ausencia registrada ese día no son candidatos.
4. Si hay **empate**, se decide por **sorteo**.
5. Se distingue `asignado_a` (le corresponde) de `realizada_por` (quien la cubre). El contador que sube es el de
   quien la **realiza**, así el asignado original recupera la prioridad en las rondas siguientes.

### Ausencias (máquina de estados)
- `generica`: `pendiente_justificante` → `justificada` → `firmada`.
- `administrativa` y `actividad_externa`: `registrada` → `firmada`.
- Para firmar es necesario haber generado antes el PDF.

### Tickets (entidad genérica de solicitudes)
- Un único modelo para los tres tipos, con un campo flexible `datos`.
- Transiciones válidas: `pendiente` → `en_curso` → `finalizado`. Solo las cambia el responsable del tipo.
- En los tickets `rrss` se genera un borrador del texto de la publicación en `datos.borrador_ia`.

### Reservas
- Dos reservas del mismo recurso se solapan si cada una empieza antes de que termine la otra → **409**.

### Transversales
- **Auditoría:** toda acción relevante queda registrada (usuario, acción, fecha y hora) → `GET /auditoria`.
- **Notificaciones:** se registran al asignar guardias, crear tickets, cambiar estados o publicar anuncios destacados.

## 9. Pruebas automatizadas (pytest)

Con el entorno virtual activo:

```bash
pytest
```

Las pruebas cubren el núcleo de autenticación y roles, el algoritmo de guardias (incluido el ejemplo de la memoria
técnica), las transiciones de tickets, el solapamiento de reservas y el flujo completo de una ausencia.

## 10. Ejecución con Docker (opcional)

```bash
docker compose up --build
```

La API queda disponible en http://127.0.0.1:8000/docs. Para pararla: `Ctrl + C` y `docker compose down`.

## 11. Contrato OpenAPI y editor.swagger.io

El fichero **`docs/openapi-intranet-santa-rosa.yaml`** es el **contrato** de la API, escrito a mano en
OpenAPI 3.0.3. Se recomienda **diseñar primero el contrato y después programar** (*API First*).

1. Abre https://editor.swagger.io.
2. **File → Import file** y selecciona el YAML (o pega su contenido en el panel izquierdo).
3. Con el servidor en marcha, pulsa **Try it out** en cualquier endpoint: el YAML apunta a `http://127.0.0.1:8000/api/v1`.

> Si el navegador bloquea las peticiones desde editor.swagger.io, usa directamente http://127.0.0.1:8000/docs,
> que muestra la misma API generada por FastAPI.

## 12. Limitaciones: qué está simulado

| Funcionalidad | En este ejemplo | En el proyecto real |
|---|---|---|
| Persistencia | Diccionarios en memoria (`app/db.py`) | MongoDB (almacén principal) + Redis (caché, sesiones, colas) |
| Login con Google | `DEMO_MODE`: el email hace de token | Verificar el `id_token` con la librería `google-auth` |
| Notificaciones | Se guardan en una lista | Web Push (`pywebpush`) y email (`fastapi-mail`) |
| Borrador RRSS | Plantilla de texto | Llamada a la API de un modelo de IA generativa |
| PDF | Generador mínimo propio | WeasyPrint o ReportLab |
| Firma manuscrita | Se registra, no se incrusta | Pillow para incrustar la imagen en el PDF |
| AutoFirma | Devuelve 501 | Integración de mejor esfuerzo |
| Justificante | Se lee pero no se guarda | Almacenamiento de ficheros (disco, GridFS u objeto) |

## 13. Publicar el proyecto en GitHub o GitLab

1. Crea un repositorio **vacío** en GitHub o GitLab (sin README ni licencia, porque ya los incluye el proyecto).
2. Desde la carpeta del proyecto:
   ```bash
   git init
   git add .
   git commit -m "feat: API de la intranet del Centro Médico Santa Rosa de Lima"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/intranet-santa-rosa-api.git
   git push -u origin main
   ```
3. Comprueba en la web del repositorio que **no** aparece el fichero `.env` ni la carpeta `.venv`.

Buenas prácticas: commits pequeños y descriptivos (evita un único «subida final») y nunca subas claves ni datos
personales reales.

## 14. Documentación pública en GitHub Pages (Swagger)

El repositorio incluye un flujo de **CI/CD** que publica la documentación interactiva de la API en
**GitHub Pages**, con el mismo aspecto que `/docs`, en una dirección pública como:

```
https://TU_USUARIO.github.io/intranet-santa-rosa-api/
```

### Cómo funciona

GitHub Pages solo sirve ficheros estáticos: **no puede ejecutar FastAPI**. Por eso, en cada `push` a `main`,
el flujo `.github/workflows/pages.yml`:

1. Instala las dependencias y **ejecuta los tests**. Si alguno falla, no se publica nada.
2. Ejecuta `scripts/export_openapi.py`, que importa la aplicación y genera `openapi.json` **a partir del código**.
   La documentación publicada nunca se desfasa respecto a la API real.
3. Publica la carpeta `site/`: la página `index.html` (Swagger UI), el `openapi.json` generado y el contrato YAML.

La página tiene un selector (**Select a definition**) para alternar entre la API **generada desde el código** y el
**contrato de diseño** (YAML). Así es fácil comprobar si la implementación cumple lo diseñado.

### Activarlo (una sola vez)

1. Sube el proyecto a GitHub (apartado 13). El repositorio debe ser **público**, o de un plan que permita Pages.
2. En el repositorio: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. Haz cualquier `push` a `main`, o ve a **Actions → Documentación de la API en GitHub Pages → Run workflow**.
4. Cuando el flujo termine (icono verde ✅), la URL aparece en **Settings → Pages** y en el resumen del flujo.

### Probar endpoints desde la página publicada («Try it out»)

La página documenta la API, pero las peticiones se envían al servidor elegido en **Servers**:

- **Servidor local** (`http://127.0.0.1:8000`): arranca la API en tu equipo con `uvicorn app.main:app` y usa la página
  publicada como cliente. La API ya permite peticiones desde otros orígenes (CORS).
  Algunos navegadores piden permiso, o bloquean, las peticiones de una web pública hacia `localhost`.
  En ese caso, usa directamente `http://127.0.0.1:8000/docs`.
- **API desplegada** (opcional): si publicas la API en un servicio de alojamiento, crea la variable
  **Settings → Secrets and variables → Actions → Variables → `PUBLIC_API_URL`** con su dirección
  (p. ej. `https://mi-api.onrender.com`). En la siguiente publicación aparecerá como primer servidor.

### Ver la página en local antes de publicarla

```bash
python scripts/export_openapi.py
python -m http.server 8080 --directory site
```

Abre http://localhost:8080. Los ficheros generados (`site/openapi.json` y `site/*.yaml`) no se suben al
repositorio: los crea el flujo de CI/CD en cada publicación.

### ¿Y en GitLab?

El fichero `.gitlab-ci.yml` hace lo mismo en **GitLab Pages**: ejecuta los tests y publica la carpeta `public/`.
Tras el primer `push`, la URL aparece en **Deploy → Pages**.

> ⚠️ La documentación publicada es **pública**. No incluyas nunca en descripciones o ejemplos datos personales reales,
> claves ni direcciones de servidores internos.

## 15. Licencia

Distribuido bajo licencia **MIT**. Consulta el fichero [LICENSE](LICENSE).
