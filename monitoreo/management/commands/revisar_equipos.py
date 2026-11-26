from django.core.management.base import BaseCommand

from monitoreo.models import Equipo
from monitoreo.services import revisar_equipo


class Command(BaseCommand):
    help = "Revisa todos los equipos con IP y actualiza si están en línea o no. Pensado para cron."

    def handle(self, *args, **opciones):
        equipos = Equipo.objects.exclude(ip__isnull=True).select_related("cliente")
        caidos = 0
        for equipo in equipos:
            revisar_equipo(equipo)
            if equipo.estado == Equipo.Estado.FUERA_DE_LINEA:
                caidos += 1
                self.stdout.write(self.style.WARNING(f"Fuera de línea: {equipo} [{equipo.ip}]"))
        self.stdout.write(
            self.style.SUCCESS(f"Revisados {equipos.count()} equipos, {caidos} fuera de línea.")
        )
