from django.contrib import admin

from .models import Cliente, Equipo, OrdenServicio


class EquipoEnLinea(admin.TabularInline):
    model = Equipo
    extra = 0
    fields = ["tipo", "ubicacion", "ip", "puerto", "estado"]
    readonly_fields = ["estado"]


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ["nombre", "tipo", "direccion", "telefono"]
    list_filter = ["tipo"]
    search_fields = ["nombre", "direccion"]
    inlines = [EquipoEnLinea]


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ["__str__", "ip", "estado", "ultima_revision"]
    list_filter = ["tipo", "estado"]
    search_fields = ["ubicacion", "ip", "cliente__nombre"]


@admin.register(OrdenServicio)
class OrdenServicioAdmin(admin.ModelAdmin):
    list_display = ["__str__", "estado", "tecnico", "fecha_programada", "creada"]
    list_filter = ["estado", "tipo"]
    search_fields = ["descripcion", "cliente__nombre"]
