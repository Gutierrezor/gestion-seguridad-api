from django.conf import settings
from django.db import models
from django.utils import timezone


class Cliente(models.Model):
    """Empresa, casa o conjunto residencial al que se le presta el servicio."""

    class Tipo(models.TextChoices):
        EMPRESA = "empresa", "Empresa"
        CASA = "casa", "Casa"
        CONJUNTO = "conjunto", "Conjunto residencial"

    nombre = models.CharField(max_length=120)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    direccion = models.CharField(max_length=200)
    telefono = models.CharField(max_length=30, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Equipo(models.Model):
    """Equipo de seguridad instalado donde un cliente."""

    class Tipo(models.TextChoices):
        CAMARA = "camara", "Cámara IP"
        NVR = "nvr", "Grabador (NVR/DVR)"
        ALARMA = "alarma", "Panel de alarma"
        CERCA = "cerca", "Cerca eléctrica"
        ROUTER = "router", "Router"

    class Estado(models.TextChoices):
        EN_LINEA = "en_linea", "En línea"
        FUERA_DE_LINEA = "fuera_de_linea", "Fuera de línea"
        SIN_REVISAR = "sin_revisar", "Sin revisar"

    # Puerto que se revisa por defecto según el tipo de equipo.
    PUERTOS_POR_DEFECTO = {
        Tipo.CAMARA: 554,  # RTSP
        Tipo.NVR: 80,
        Tipo.ALARMA: 4370,
        Tipo.CERCA: 80,
        Tipo.ROUTER: 80,
    }

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="equipos")
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    marca = models.CharField(max_length=60, blank=True)
    modelo = models.CharField(max_length=60, blank=True)
    ubicacion = models.CharField(max_length=120, help_text="Ej.: portería, parqueadero, bodega")
    ip = models.GenericIPAddressField(null=True, blank=True)
    puerto = models.PositiveIntegerField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.SIN_REVISAR)
    ultima_revision = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["cliente__nombre", "tipo", "ubicacion"]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.ubicacion} ({self.cliente})"

    @property
    def puerto_a_revisar(self):
        return self.puerto or self.PUERTOS_POR_DEFECTO.get(self.tipo, 80)


class OrdenServicio(models.Model):
    """Visita técnica: instalación, mantenimiento o atención de una falla."""

    class Tipo(models.TextChoices):
        INSTALACION = "instalacion", "Instalación"
        MANTENIMIENTO = "mantenimiento", "Mantenimiento"
        FALLA = "falla", "Falla"
        FALSA_ALARMA = "falsa_alarma", "Falsa alarma"

    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        EN_PROCESO = "en_proceso", "En proceso"
        CERRADA = "cerrada", "Cerrada"

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="ordenes")
    equipo = models.ForeignKey(
        Equipo, on_delete=models.SET_NULL, null=True, blank=True, related_name="ordenes"
    )
    tecnico = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    descripcion = models.TextField()
    solucion = models.TextField(blank=True)
    fecha_programada = models.DateField(null=True, blank=True)
    creada = models.DateTimeField(auto_now_add=True)
    cerrada_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-creada"]
        verbose_name = "orden de servicio"
        verbose_name_plural = "órdenes de servicio"

    def __str__(self):
        return f"#{self.pk} {self.get_tipo_display()} - {self.cliente}"

    def cerrar(self, solucion):
        """Cierra la orden guardando qué se hizo y cuándo."""
        self.estado = self.Estado.CERRADA
        self.solucion = solucion
        self.cerrada_en = timezone.now()
        self.save(update_fields=["estado", "solucion", "cerrada_en"])
