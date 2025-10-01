from django.contrib import admin
from django.utils.html import format_html, format_html_join
from django.utils.translation import gettext_lazy as _
from .models import (
    Brand,
    Category,
    Color,
    Size,
    Product,
    ProductImage,
    ProductVariation,
)


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "hex_code")
    search_fields = ("name", "code")
    list_editable = ("code", "hex_code")


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "sort_order")
    list_editable = ("code", "sort_order")
    search_fields = ("name", "code")
    ordering = ("sort_order", "name")


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0


class ProductVariationInline(admin.TabularInline):
    model = ProductVariation
    extra = 0
    fields = ("color", "size", "sku", "price_override", "stock", "is_active")
    autocomplete_fields = ("color", "size")
    show_change_link = True


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "brand",
        "category",
        "is_active",
        "created_at",
        "available_colors",
        "variation_count",
    )
    list_filter = ("is_active", "brand", "category")
    search_fields = ("name", "brand__name", "category__name")
    inlines = [ProductImageInline, ProductVariationInline]
    readonly_fields = ("variation_matrix_html",)
    fieldsets = (
        (
            None,
            {"fields": ("name", "slug", "brand", "category", "image", "description")},
        ),
        (_("قیمت‌ها/وضعیت"), {"fields": ("price", "discount_price", "is_active")}),
        (_("خلاصه تنوع‌ها"), {"fields": ("variation_matrix_html",)}),
    )

    @admin.display(description=_("رنگ‌های موجود"))
    def available_colors(self, obj: Product):
        qs = (
            obj.variations.filter(is_active=True, color__isnull=False)
            .values_list("color__name", flat=True)
            .distinct()
        )
        return ", ".join(qs) or "—"

    @admin.display(description=_("تعداد واریانت‌ها"))
    def variation_count(self, obj: Product):
        return obj.variations.count()

    @admin.display(description=_("ماتریس رنگ × سایز"), ordering=None)
    def variation_matrix_html(self, obj: Product):
        """
        خروجی HTML برای نمایش جدول/لیست:
        - هر رنگ، کد رنگ (Color.code) را هم نشان می‌دهد.
        - زیر هر رنگ، لیست سایزها با کد سایز (Size.code) و موجودی.
        """

        matrix = {}
        for v in obj.variations.select_related("color", "size"):
            color = v.color
            size = v.size
            key = color.id if color else 0
            if key not in matrix:
                matrix[key] = {
                    "name": color.name if color else "—",
                    "code": color.code if color else "",
                    "rows": [],
                }
            matrix[key]["rows"].append(
                (
                    size.name if size else "—",
                    size.code if size else "",
                    v.sku,
                    v.stock,
                )
            )

        if not matrix:
            return "واریانتی ثبت نشده است."

        parts = []
        for _, col in sorted(matrix.items(), key=lambda x: x[1]["name"]):
            head = f"<strong>{col['name']}</strong>"
            if col["code"]:
                head += f" <span class='text-muted'>({col['code']})</span>"
            lines = format_html_join(
                "",
                "<li>{} <span class='text-muted'>({})</span> — SKU: <code>{}</code> — {} عدد</li>",
                ((r[0], r[1] or "—", r[2], r[3]) for r in sorted(col["rows"])),
            )
            parts.append(
                format_html(
                    "<div style='margin-bottom:.5rem'>{}<ul style='margin:.25rem 0 .5rem 1rem'>{}</ul></div>",
                    format_html(head),
                    lines,
                )
            )

        return format_html("".join(parts))


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "parent", "is_active")
    list_filter = ("is_active", "parent")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
