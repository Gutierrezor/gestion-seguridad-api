from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("clientes", views.ClienteViewSet)
router.register("equipos", views.EquipoViewSet)
router.register("ordenes", views.OrdenServicioViewSet)

urlpatterns = [
    path("token/", obtain_auth_token, name="token"),
    path("resumen/", views.resumen, name="resumen"),
    path("", include(router.urls)),
]
