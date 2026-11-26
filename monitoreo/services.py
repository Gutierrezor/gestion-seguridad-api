"""Lógica para revisar si un equipo responde en la red."""

import socket

from django.conf import settings
from django.utils import timezone

from .models import Equipo


def puerto_abierto(ip, puerto, espera):
    """Devuelve True si se puede abrir una conexión TCP con el equipo."""
    try:
        with socket.create_connection((ip, puerto), timeout=espera):
            return True
    except OSError:
        return False


def revisar_equipo(equipo, espera=None):
    """
    Revisa un equipo y guarda su estado.

    Se usa una conexión TCP en vez de ping porque muchas redes bloquean el
    ping y porque así sabemos que el servicio (RTSP, web, etc.) está arriba.
    """
    if not equipo.ip:
        equipo.estado = Equipo.Estado.SIN_REVISAR
    else:
        espera = espera if espera is not None else settings.TIEMPO_ESPERA_REVISION
        responde = puerto_abierto(equipo.ip, equipo.puerto_a_revisar, espera)
        equipo.estado = Equipo.Estado.EN_LINEA if responde else Equipo.Estado.FUERA_DE_LINEA
    equipo.ultima_revision = timezone.now()
    equipo.save(update_fields=["estado", "ultima_revision"])
    return equipo
