from rest_framework import serializers

from .models import Cliente, Equipo, OrdenServicio


class ClienteSerializer(serializers.ModelSerializer):
    total_equipos = serializers.IntegerField(source="equipos.count", read_only=True)

    class Meta:
        model = Cliente
        fields = ["id", "nombre", "tipo", "direccion", "telefono", "total_equipos", "creado"]


class EquipoSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source="cliente.nombre", read_only=True)

    class Meta:
        model = Equipo
        fields = [
            "id", "cliente", "cliente_nombre", "tipo", "marca", "modelo", "ubicacion",
            "ip", "puerto", "estado", "ultima_revision",
        ]
        read_only_fields = ["estado", "ultima_revision"]


class OrdenServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdenServicio
        fields = [
            "id", "cliente", "equipo", "tecnico", "tipo", "estado", "descripcion",
            "solucion", "fecha_programada", "creada", "cerrada_en",
        ]
        read_only_fields = ["solucion", "creada", "cerrada_en"]

    def validate(self, datos):
        equipo = datos.get("equipo")
        cliente = datos.get("cliente") or getattr(self.instance, "cliente", None)
        if equipo and cliente and equipo.cliente_id != cliente.id:
            raise serializers.ValidationError(
                {"equipo": "El equipo no pertenece a este cliente."}
            )
        return datos


class CerrarOrdenSerializer(serializers.Serializer):
    solucion = serializers.CharField()
