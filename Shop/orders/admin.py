from django.contrib import admin
from .models import Order, OrderItem, Coupon


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product_name", "sku", "price", "quantity", "line_total")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "status",
        "subtotal",
        "discount_amount",
        "shipping_cost",
        "total",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "id",
        "user__username",
        "user__email",
        "full_name",
        "phone",
        "coupon_code",
    )
    inlines = [OrderItemInline]
    readonly_fields = ("created_at",)


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "percent_off",
        "amount_off",
        "is_active",
        "starts_at",
        "ends_at",
        "used_count",
        "usage_limit",
    )
    list_filter = ("is_active",)
    search_fields = ("code",)
