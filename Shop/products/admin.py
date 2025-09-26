from django.contrib import admin
from .models import Category, Brand, Color, Size, Product, ProductImage, ProductVariation


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "is_active")
    list_filter = ("is_active", "parent")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ("name", "sort_order")
    list_editable = ("sort_order",)
    search_fields = ("name",)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image", "alt_text", "is_main")
    classes = ("collapse",)


class ProductVariationInline(admin.TabularInline):
    model = ProductVariation
    extra = 1
    fields = ("color", "size", "sku", "barcode", "price_override", "stock", "is_active", "image")
    show_change_link = True


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "brand", "category", "price", "discount_price", "is_active", "total_stock")
    list_filter = ("is_active", "brand", "category")
    search_fields = ("name", "slug", "brand__name", "category__name")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline, ProductVariationInline]

    def total_stock(self, obj):
        return obj.stock_total()
    total_stock.short_description = "موجودی کل"
