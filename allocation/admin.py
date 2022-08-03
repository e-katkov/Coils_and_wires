from django.contrib import admin

from allocation.models import AllocationDB, CoilDB, OrderLineDB


@admin.register(CoilDB)
class CoilDBAdmin(admin.ModelAdmin):
    list_display = ('id', 'reference', 'product_id', 'quantity', 'recommended_balance', 'acceptable_loss')
    list_filter = ('product_id',)
    search_fields = ('reference', 'product_id')
    fieldsets = (
        ('Информация о бухте', {'fields': ('reference',)}),
        ('Информация о материале', {'fields': ('product_id', 'quantity', 'recommended_balance', 'acceptable_loss')})
    )


@admin.register(OrderLineDB)
class OrderLineDBAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_id', 'line_item', 'product_id', 'quantity')
    list_filter = ('order_id', 'product_id')
    search_fields = ('order_id', 'line_item', 'product_id')
    fieldsets = (
        ('Информация о заказе', {'fields': ('order_id', 'line_item')}),
        ('Информация о материале', {'fields': ('product_id', 'quantity')})
    )


@admin.register(AllocationDB)
class AllocationDBAdmin(admin.ModelAdmin):
    list_display = ('id', 'coil_record', 'orderline_record')
    list_filter = ('coil_record', 'orderline_record')
    search_fields = ('coil_record', 'orderline_record')
