from django.core.management.base import BaseCommand

from monitoreo.models import Cliente, Equipo, OrdenServicio


class Command(BaseCommand):
    help = "Crea datos de ejemplo para probar la API rápidamente."

    def handle(self, *args, **opciones):
        if Cliente.objects.exists():
            self.stdout.write("Ya hay datos, no se cargó nada.")
            return

        conjunto = Cliente.objects.create(
            nombre="Conjunto Los Pinos", tipo="conjunto", direccion="Calle 10 # 5-20, Neiva"
        )
        empresa = Cliente.objects.create(
            nombre="Ferretería El Tornillo", tipo="empresa", direccion="Cra 7 # 8-10, Neiva"
        )

        camara = Equipo.objects.create(
            cliente=conjunto, tipo="camara", marca="Hikvision", ubicacion="Portería", ip="192.168.1.50"
        )
        Equipo.objects.create(
            cliente=conjunto, tipo="nvr", marca="Dahua", ubicacion="Cuarto técnico", ip="192.168.1.10"
        )
        Equipo.objects.create(cliente=conjunto, tipo="cerca", ubicacion="Muro norte")
        Equipo.objects.create(
            cliente=empresa, tipo="alarma", marca="DSC", ubicacion="Bodega", ip="192.168.0.20"
        )

        OrdenServicio.objects.create(
            cliente=conjunto, equipo=camara, tipo="falla",
            descripcion="La cámara de portería no da imagen en la noche.",
        )
        OrdenServicio.objects.create(
            cliente=empresa, tipo="mantenimiento", descripcion="Mantenimiento preventivo trimestral."
        )
        self.stdout.write(self.style.SUCCESS("Datos de ejemplo cargados."))
