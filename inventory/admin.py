
from django.contrib import admin
from .models import Category, Product, Warehouse, InventoryBalance, StockMovement


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "category", "cost_price", "selling_price", "is_active")
    search_fields = ("sku", "name")
    list_filter = ("category", "is_active")


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active")
    search_fields = ("code", "name")


@admin.register(InventoryBalance)
class InventoryBalanceAdmin(admin.ModelAdmin):
    list_display = ("product", "warehouse", "quantity")
    readonly_fields = ("product", "warehouse", "quantity")
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("reference", "product", "warehouse", "movement_type", "quantity", "created_at")
    readonly_fields = [field.name for field in StockMovement._meta.fields]
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
