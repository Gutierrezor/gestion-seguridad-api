# Gestión de Seguridad API

API REST hecha con **Django** y **Django REST Framework** para manejar el trabajo de una empresa de seguridad electrónica: clientes, equipos instalados (cámaras, grabadores, alarmas, cercas eléctricas, routers) y órdenes de servicio de los técnicos.

La idea sale de mi trabajo como técnico en seguridad electrónica: saber rápido qué equipos están caídos, qué visitas hay pendientes y qué se hizo en cada una.

![Pruebas](https://github.com/Gutierrezor/gestion-seguridad-api/actions/workflows/pruebas.yml/badge.svg)

## Qué hace

- **Clientes:** empresas, casas y conjuntos residenciales, con búsqueda por nombre o dirección.
- **Equipos:** inventario de lo que está instalado en cada cliente, con su IP y puerto.
- **Revisión de equipos:** revisa si un equipo responde en la red y guarda si está en línea o fuera de línea. Usa una conexión TCP al puerto del servicio (por ejemplo RTSP 554 en cámaras), porque muchas redes bloquean el ping.
- **Órdenes de servicio:** instalaciones, mantenimientos, fallas y falsas alarmas. Se pueden cerrar guardando la solución aplicada.
- **Resumen:** un endpoint con cuántos equipos hay por estado, las órdenes abiertas y la lista de equipos caídos.
- **Revisión automática:** un comando (`revisar_equipos`) para correr con cron cada cierto tiempo.

## Tecnologías

Python 3.12 · Django 5.1 · Django REST Framework · django-filter · PostgreSQL · Docker y Docker Compose · GitHub Actions

## Cómo correrlo

### Con Docker (recomendado)

```bash
cp .env.example .env          # y cambia las claves
docker compose up --build
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py cargar_demo   # datos de ejemplo
```

La API queda en `http://localhost:8000/api/` y el panel de administración en `http://localhost:8000/admin/`.

### Sin Docker (usa SQLite)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py cargar_demo
python manage.py runserver
```

## Endpoints

Todos piden estar autenticado (token o sesión).

| Método | Ruta | Qué hace |
|---|---|---|
| POST | `/api/token/` | Devuelve el token con usuario y contraseña |
| GET, POST | `/api/clientes/` | Lista o crea clientes (`?search=`, `?tipo=`) |
| GET, POST | `/api/equipos/` | Lista o crea equipos (`?cliente=`, `?tipo=`, `?estado=`) |
| POST | `/api/equipos/{id}/revisar/` | Revisa ya mismo si el equipo responde |
| GET, POST | `/api/ordenes/` | Lista o crea órdenes (`?estado=`, `?tipo=`, `?tecnico=`) |
| POST | `/api/ordenes/{id}/cerrar/` | Cierra la orden con la solución |
| GET | `/api/resumen/` | Resumen para un panel |

### Ejemplo

```bash
# 1. Pedir el token
curl -X POST http://localhost:8000/api/token/ -d "username=admin&password=tu-clave"

# 2. Revisar una cámara
curl -X POST http://localhost:8000/api/equipos/1/revisar/ -H "Authorization: Token TU_TOKEN"

# 3. Cerrar una orden
curl -X POST http://localhost:8000/api/ordenes/1/cerrar/ \
     -H "Authorization: Token TU_TOKEN" \
     -d "solucion=Se cambió el conector RJ45 de la cámara"
```

## Revisión automática con cron

Para revisar todos los equipos cada 10 minutos:

```cron
*/10 * * * * cd /ruta/al/proyecto && docker compose exec -T web python manage.py revisar_equipos
```

## Pruebas

```bash
python manage.py test
```

Hay pruebas para la autenticación, los clientes, la revisión de equipos (simulando la red), el cierre de órdenes, el resumen y el comando de cron. Se corren solas en cada push con GitHub Actions.

## Estructura

```
config/            Configuración de Django (settings, urls)
monitoreo/
  models.py        Cliente, Equipo y OrdenServicio
  services.py      Lógica para revisar si un equipo responde
  serializers.py   Validaciones de la API
  views.py         Endpoints
  management/      Comandos revisar_equipos y cargar_demo
  tests.py         Pruebas
```

## Ideas para seguir

- Avisos por Telegram o correo cuando un equipo se cae.
- Historial de cambios de estado de cada equipo.
- Fotos y firma del cliente al cerrar una orden.

---

Hecho por **Julián Andrés Gutiérrez Ordóñez** · [LinkedIn](https://www.linkedin.com/in/julianandresgutierrez) · [Portafolio](https://portafolio-julian-psi.vercel.app/)
