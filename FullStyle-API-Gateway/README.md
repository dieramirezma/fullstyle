# FullStyle GraphQL API Gateway

Este proyecto proporciona un **GraphQL API Gateway** que unifica todos los microservicios de FullStyle en una sola interfaz GraphQL utilizando **Apollo Server** y **GraphQL Mesh**.

## 🚀 Características

- **Apollo Server** con GraphQL Mesh integrado
- **Unificación de APIs**: Combina múltiples APIs REST en una sola API GraphQL
- **Autodetección de esquemas**: Genera automáticamente esquemas GraphQL desde especificaciones OpenAPI
- **Hot reload**: Desarrollo con recarga automática
- **Tipado fuerte**: TypeScript con tipos generados automáticamente

## 📋 Microservicios Integrados

| Servicio | Tecnología | URL Base | Descripción |
|----------|------------|----------|-------------|
| `fs_ms_au` | Go | http://localhost:5001/api/ | Servicio de autenticación |
| `fs_ms_lc` | Python/Flask | http://localhost:5000/api/ | Servicio de lógica central |
| `fs_ms_cb` | Python | http://localhost:8000/api/v1/ | Servicio de chatbot |

## 🛠️ Instalación y Configuración

### Requisitos Previos

- [Node.js](https://nodejs.org/) (v18 o superior)
- [pnpm](https://pnpm.io/) (gestor de paquetes)
- Los microservicios ejecutándose en sus respectivos puertos

### Instalación

```bash
# Clonar el repositorio
git clone <repository-url>
cd FullStyle-API-Gateway

# Instalar dependencias
pnpm install

# Generar esquemas GraphQL desde OpenAPI
pnpm mesh:generate
```

### Ejecución

```bash
# Desarrollo (con hot reload)
pnpm dev

# Producción
pnpm build
pnpm start
```

El servidor estará disponible en: **http://localhost:4000**

## 📖 Uso

### GraphQL Playground

Accede a http://localhost:4000 para abrir Apollo Studio y explorar la API GraphQL unificada.

### Consultas de Ejemplo

```graphql
# Obtener información de un usuario
query GetUser {
  user_by_id(id: 1) {
    id
    name
    email
    active
  }
}

# Obtener sitios
query GetSites {
  site {
    id
    name
    address
    phone
    manager_id
  }
}

# Obtener citas
query GetAppointments {
  appointment(status: "confirmed") {
    id
    appointmenttime
    status
    worker_id
    site_id
    service_id
    client_id
  }
}

# Usar el chatbot
mutation SendChatMessage {
  post_send(input: {
    message: "Hola, necesito ayuda"
    session_id: "session123"
  }) {
    ... on ChatResponse {
      reply
      session_id
    }
  }
}
```

### Mutaciones de Ejemplo

```graphql
# Crear una nueva cita
mutation CreateAppointment {
  post_appointment(input: {
    appointmenttime: "2025-06-15T10:00:00Z"
    worker_id: 1
    site_id: 1
    service_id: 1
    client_id: 1
    status: "pending"
  }) {
    message
    appointment
  }
}

# Iniciar sesión
mutation Login {
  post_login(input: {
    email: "user@example.com"
    password: "password123"
  }) {
    user
    access_token
    refresh_token
  }
}
```

## 🔧 Scripts Disponibles

| Script | Descripción |
|--------|-------------|
| `pnpm dev` | Ejecuta el servidor en modo desarrollo |
| `pnpm build` | Compila el proyecto para producción |
| `pnpm start` | Ejecuta el servidor compilado |
| `pnpm mesh:generate` | Regenera los esquemas GraphQL desde OpenAPI |
| `pnpm mesh:dev` | Ejecuta solo GraphQL Mesh en modo desarrollo |

## 📁 Estructura del Proyecto

```
FullStyle-API-Gateway/
├── .mesh/                   # Esquemas y tipos generados por GraphQL Mesh
│   ├── index.ts            # Punto de entrada del mesh
│   ├── schema.graphql      # Esquema GraphQL unificado
│   └── sources/            # Esquemas individuales por servicio
├── src/
│   ├── index.ts            # Servidor Apollo con Mesh integrado
│   ├── resolvers/          # Resolvers personalizados (legacy)
│   └── schema/             # Esquemas GraphQL personalizados (legacy)
├── .meshrc.yml             # Configuración de GraphQL Mesh
├── package.json
├── tsconfig.json
└── README.md
```

## ⚙️ Configuración

La configuración de GraphQL Mesh se encuentra en `.meshrc.yml`:

```yaml
sources:
  - name: fs_ms_au
    handler:
      openapi:
        source: ./../FullStyle-Backend-Go/docs/swagger.yaml
        baseUrl: http://localhost:5000/
  - name: fs_ms_lc
    handler:
      openapi:
        source: ./../FullStyle-Backend/swagger/swagger.yaml
        baseUrl: http://localhost:5000/api/
  - name: fs_ms_cb
    handler:
      openapi:
        source: ./../FullStyle-Chatbot/openapi.yaml
        baseUrl: http://localhost:8080/api/v1/
```

## 🐛 Resolución de Problemas

### Error: Cannot find module '.mesh'

```bash
pnpm mesh:generate
```

### Error de conexión a microservicios

Verificar que todos los microservicios estén ejecutándose:

```bash
# Verificar servicios
curl http://localhost:5000/health    # FullStyle-Backend-Go
curl http://localhost:5000/api/      # FullStyle-Backend
curl http://localhost:8080/api/v1/   # FullStyle-Chatbot
```

### Regenerar esquemas

Si cambias las especificaciones OpenAPI de los microservicios:

```bash
pnpm mesh:generate
```

## 🔄 Integración con Docker

### API Gateway con NGINX y Microservicios

Este repositorio también contiene la configuración de un API Gateway basado en NGINX que orquesta el acceso a varios microservicios desarrollados en diferentes tecnologías (Flask, Go, Chatbot en Python) y un frontend en Next.js.

### Requisitos Previos para Docker

- Tener instalado [Docker](https://docs.docker.com/get-docker/) y [Docker Compose](https://docs.docker.com/compose/install/).
- Tener instalado [Git](https://git-scm.com/).
- (Opcional) Tener instalado [PostgreSQL](https://www.postgresql.org/download/) si deseas gestionar la base de datos manualmente.

### Instalación de la Base de Datos (Postgres)

1. **Crear un contenedor de Postgres (recomendado):**

   Puedes agregar el siguiente servicio a tu `docker-compose.yaml` o ejecutarlo aparte:

   ```yaml
   postgres:
     image: postgres:15
     restart: always
     environment:
       POSTGRES_USER: tu_usuario
       POSTGRES_PASSWORD: tu_password
       POSTGRES_DB: tu_basededatos
     ports:
       - "5432:5432"
     volumes:
       - ./backup.dump:/docker-entrypoint-initdb.d/backup.dump
   ```

   Esto levantará una base de datos y restaurará el backup si existe el archivo `backup.dump` en la raíz del proyecto.

2. **Restaurar backup manualmente (si es necesario):**

   Si tienes un backup y quieres restaurarlo manualmente:

   ```bash
   psql -U tu_usuario -d tu_basededatos -f backup.dump
   ```

   Asegúrate de que las variables de entorno de cada microservicio apunten a la base de datos correcta.

## Tabla de Contenidos
- [Requisitos Previos](#requisitos-previos)
- [Instalación de la Base de Datos (Postgres)](#instalación-de-la-base-de-datos-postgres)
- [Ejecución de los Servicios](#ejecución-de-los-servicios)
- [Rutas de Acceso](#rutas-de-acceso)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Notas y Consejos](#notas-y-consejos)

---

## Requisitos Previos

- Tener instalado [Docker](https://docs.docker.com/get-docker/) y [Docker Compose](https://docs.docker.com/compose/install/).
- Tener instalado [Git](https://git-scm.com/).
- (Opcional) Tener instalado [PostgreSQL](https://www.postgresql.org/download/) si deseas gestionar la base de datos manualmente.

## Instalación de la Base de Datos (Postgres)

1. **Crear un contenedor de Postgres (recomendado):**

   Puedes agregar el siguiente servicio a tu `docker-compose.yaml` o ejecutarlo aparte:

   ```yaml
   postgres:
     image: postgres:15
     restart: always
     environment:
       POSTGRES_USER: tu_usuario
       POSTGRES_PASSWORD: tu_password
       POSTGRES_DB: tu_basededatos
     ports:
       - "5432:5432"
     volumes:
       - ./backup.dump:/docker-entrypoint-initdb.d/backup.dump
   ```

   Esto levantará una base de datos y restaurará el backup si existe el archivo `backup.dump` en la raíz del proyecto.

2. **Restaurar backup manualmente (si es necesario):**

   Si tienes un backup y quieres restaurarlo manualmente:

   ```bash
   psql -U tu_usuario -d tu_basededatos -f backup.dump
   ```

   Asegúrate de que las variables de entorno de cada microservicio apunten a la base de datos correcta.

## Ejecución de los Servicios

1. Clona todos los repositorios de los microservicios en la misma carpeta (como subcarpetas de este proyecto).
2. Asegúrate de estar en la rama `develop` de cada repositorio.
3. Coloca los archivos `.env` en la raíz de cada microservicio.
4. Levanta todos los servicios con:

   ```bash
   docker-compose up --build
   ```

   Esto construirá y levantará:
   - Backend Flask (Python)
   - Backend Go
   - Chatbot (Python)
   - Frontend (Next.js)
   - NGINX (API Gateway)

## Rutas de Acceso

- **Backend Flask:**
  - http://localhost/flask/api/
- **Backend Go:**
  - http://localhost/go/api/
- **Chatbot:**
  - http://localhost/chatbot/api/v1/
- **Frontend:**
  - http://localhost/

## Estructura del Proyecto

```
fullstyle2/
├── FullStyle-Backend/        # Backend en Flask
├── FullStyle-Backend-Go/     # Backend en Go
├── FullStyle-Chatbot/        # Chatbot en Python
├── FullStyle-Frontend/       # Frontend en Next.js
├── nginx.conf                # Configuración de NGINX
├── docker-compose.yaml       # Orquestación de servicios
├── backup.dump               # Backup de la base de datos (opcional)
└── README.md                 # Este instructivo
```

## Notas y Consejos

- Si modificas la configuración de NGINX, reinicia el servicio para aplicar los cambios.
- Puedes monitorear los logs de cada servicio usando Docker Compose:
  ```bash
  docker-compose logs -f nombre_servicio
  ```
- Si tienes problemas de conexión a la base de datos, revisa las variables de entorno y la red de Docker.
- Para desarrollo, puedes exponer otros puertos según lo requieras.

## Ejecutar o Detener un Solo Servicio

Si necesitas ejecutar o detener únicamente uno de los servicios definidos en el `docker-compose.yaml`, puedes hacerlo fácilmente usando los siguientes comandos desde la raíz del proyecto:

### Ejecutar un solo servicio

```powershell
docker-compose up nombre_servicio
```
Por ejemplo, para levantar solo el backend en Flask:
```powershell
docker-compose up flask
```

### Detener un solo servicio

```powershell
docker-compose stop nombre_servicio
```
Por ejemplo, para detener solo el frontend:
```powershell
docker-compose stop frontend
```

### Reiniciar un servicio

```powershell
docker-compose restart nombre_servicio
```

Puedes consultar los nombres exactos de los servicios en el archivo `docker-compose.yaml`.

---

¿Dudas o problemas? Revisa los README.md de cada microservicio o contacta al equipo de desarrollo.


