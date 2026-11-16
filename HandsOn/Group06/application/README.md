# Aplicación Web Semántica

Aplicación web desarrollada como parte del proyecto de **Web Semántica**, utilizando tecnologías modernas para el desarrollo del frontend y backend.

## Estructura
```
application/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   ├── core/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   └── requirements.txt
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── layouts/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── context/
│   │   ├── utils/
│   │   ├── styles/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   └── package.json
│
├── .gitignore
└── README.md
```

## Requisitos previos

Antes de comenzar, es necesario tener instalado:

- Python.
- Node.js y npm.

## Instalación y ejecución

### 1. Configurar el backend

Acceder a la carpeta del backend:

```bash
cd backend
```

Crear un entorno virtual:

```bash
python -m venv .venv
```

Activar el entorno virtual:

**Linux:**
```bash
source .venv/bin/activate
```

**Windows:**
```bash
.venv/Scripts/activate
```

Instalar las dependencias:

```bash
pip install -r requirements.txt
```

Iniciar el servidor:

```bash
uvicorn app.main:app --reload
```

El backend estará disponible en:

- API: http://localhost:8000
- Documentación Swagger: http://localhost:8000/docs
- Documentación ReDoc: http://localhost:8000/redoc

### 2. Configurar el frontend

Abrir otra terminal y acceder a la carpeta del frontend:

```bash
cd frontend
```

Instalar las dependencias:

```bash
npm install
```

Iniciar el servidor de desarrollo:

```bash
npm run dev
```

El frontend estará disponible en:

http://localhost:5173

## Organización del código

### Backend

El backend se organiza en diferentes módulos según su responsabilidad:

- `api/routes/`: define los endpoints de la API.
- `core/`: contiene la configuración y funcionalidades comunes.
- `schemas/`: define los esquemas de datos y validación.
- `services/`: contiene la lógica de negocio y las operaciones con servicios externos.

### Frontend

El frontend se organiza en los siguientes módulos:

- `assets/`: imágenes, iconos y fuentes.
- `components/`: componentes reutilizables de React.
- `pages/`: páginas de la aplicación.
- `layouts/`: estructuras comunes de las páginas.
- `services/`: comunicación con el backend.
- `hooks/`: hooks personalizados de React.
- `context/`: gestión del estado global.
- `utils/`: funciones auxiliares.
- `styles/`: hojas de estilos.
