from django.db.models import Count
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from .models import Cliente, Equipo, OrdenServicio
from .serializers import (
    CerrarOrdenSerializer,
    ClienteSerializer,
    EquipoSerializer,
    OrdenServicioSerializer,
)
from .services import revisar_equipo


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    filterset_fields = ["tipo"]
    search_fields = ["nombre", "direccion"]


class EquipoViewSet(viewsets.ModelViewSet):
    queryset = Equipo.objects.select_related("cliente")
    serializer_class = EquipoSerializer
    filterset_fields = ["cliente", "tipo", "estado"]
    search_fields = ["ubicacion", "marca", "modelo", "ip"]

    @action(detail=True, methods=["post"])
    def revisar(self, request, pk=None):
        """Revisa en este momento si el equipo responde en la red."""
        equipo = revisar_equipo(self.get_object())
        return Response(self.get_serializer(equipo).data)


class OrdenServicioViewSet(viewsets.ModelViewSet):
    queryset = OrdenServicio.objects.select_related("cliente", "equipo", "tecnico")
    serializer_class = OrdenServicioSerializer
    filterset_fields = ["cliente", "estado", "tipo", "tecnico"]
    search_fields = ["descripcion", "cliente__nombre"]
    ordering_fields = ["creada", "fecha_programada"]

    @action(detail=True, methods=["post"])
    def cerrar(self, request, pk=None):
        """Cierra la orden con la solución que se aplicó."""
        orden = self.get_object()
        if orden.estado == OrdenServicio.Estado.CERRADA:
            return Response(
                {"detalle": "La orden ya está cerrada."}, status=status.HTTP_400_BAD_REQUEST
            )
        datos = CerrarOrdenSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        orden.cerrar(datos.validated_data["solucion"])
        return Response(self.get_serializer(orden).data)


@api_view(["GET"])
def resumen(request):
    """Panel rápido: cuántos equipos hay por estado y cuántas órdenes abiertas."""
    equipos = {
        fila["estado"]: fila["total"]
        for fila in Equipo.objects.values("estado").annotate(total=Count("id"))
    }
    abiertas = (
        OrdenServicio.objects.exclude(estado=OrdenServicio.Estado.CERRADA)
        .values("tipo")
        .annotate(total=Count("id"))
    )
    return Response(
        {
            "clientes": Cliente.objects.count(),
            "equipos": {estado: equipos.get(estado, 0) for estado in Equipo.Estado.values},
            "ordenes_abiertas": {fila["tipo"]: fila["total"] for fila in abiertas},
            "equipos_fuera_de_linea": list(
                Equipo.objects.filter(estado=Equipo.Estado.FUERA_DE_LINEA).values(
                    "id", "cliente__nombre", "ubicacion", "ip"
                )
            ),
        }
    )
