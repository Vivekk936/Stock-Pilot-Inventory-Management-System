from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import DjangoModelPermissions

from .models import Supplier
from .serializers import SupplierSerializer


class SupplierViewSet(ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    filterset_fields = ["is_active"]
    search_fields = ["code", "name", "email"]