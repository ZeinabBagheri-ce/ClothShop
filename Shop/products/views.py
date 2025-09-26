from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Prefetch
from .models import (
    Product, ProductImage, ProductVariation,
    Category, Brand
)

def product_list(request):
    qs = (
        Product.objects.filter(is_active=True)
        .select_related("brand", "category")
        .prefetch_related(
            Prefetch("images", queryset=ProductImage.objects.order_by("-is_main")),
            Prefetch("variations", queryset=ProductVariation.objects.filter(is_active=True)),
        )
        .order_by("-created_at")
    )

    # ----- جستجو (q) -----
    q = request.GET.get("q")
    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(description__icontains=q) |
            Q(brand__name__icontains=q)
        )

    # ----- فیلتر دسته/برند -----
    brand = request.GET.get("brand")
    if brand:
        qs = qs.filter(brand__slug=brand)

    cat = request.GET.get("cat")
    if cat:
        qs = qs.filter(category__slug=cat)

    # ----- صفحه‌بندی -----
    paginator = Paginator(qs, 12)
    products = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "products/product_list.html",
        {
            "products": products,
            "query": q,
            "active_brand": brand,
            "active_category": cat,
        },
    )


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    qs = (
        Product.objects.filter(is_active=True, category=category)
        .select_related("brand", "category")
        .prefetch_related(
            Prefetch("images", queryset=ProductImage.objects.order_by("-is_main")),
            Prefetch("variations", queryset=ProductVariation.objects.filter(is_active=True)),
        )
        .order_by("-created_at")
    )
    paginator = Paginator(qs, 12)
    products = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "products/product_list.html",
        {
            "products": products,
            "active_category": category.slug,  # یا خود category اگر در تمپلیت لازم داری
        },
    )


def brand_detail(request, slug):
    brand = get_object_or_404(Brand, slug=slug)
    qs = (
        Product.objects.filter(is_active=True, brand=brand)
        .select_related("brand", "category")
        .prefetch_related(
            Prefetch("images", queryset=ProductImage.objects.order_by("-is_main")),
            Prefetch("variations", queryset=ProductVariation.objects.filter(is_active=True)),
        )
        .order_by("-created_at")
    )
    paginator = Paginator(qs, 12)
    products = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "products/product_list.html",
        {
            "products": products,
            "active_brand": brand.slug,  # یا خود brand اگر در تمپلیت لازم داری
        },
    )


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("brand", "category")
        .prefetch_related(
            Prefetch("images", queryset=ProductImage.objects.order_by("-is_main", "id")),
            Prefetch(
                "variations",
                queryset=ProductVariation.objects.filter(is_active=True)
                .select_related("color", "size"),
            ),
        ),
        slug=slug,
        is_active=True,
    )

    # دیتا برای JS: هر واریانت با قیمت/موجودی/تصویر/کد
    variants = []
    for v in product.variations.all():
        variants.append({
            "id": v.id,
            "color_id": v.color_id,
            "color": v.color.name if v.color else "",
            "color_code": getattr(v.color, "code", "") if v.color else "",
            "size_id": v.size_id,
            "size": v.size.name if v.size else "",
            "price": str(v.final_price),
            "stock": v.stock,
            "image": v.image.url if v.image else (product.image.url if product.image else ""),
            "sku": v.sku,
        })

    return render(
        request,
        "products/product_detail.html",
        {
            "product": product,
            "variants": variants,  # برای اسکریپت صفحهٔ جزئیات
        },
    )
