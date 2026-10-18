
from django.contrib import admin
from .models import Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "email", "phone", "is_active")
    search_fields = ("code", "name", "email")
    list_filter = ("is_active",)
