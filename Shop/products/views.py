from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Prefetch, OuterRef, Subquery, F, DecimalField
from django.db.models.functions import Coalesce

from .models import (
    Product,
    ProductImage,
    ProductVariation,
    Category,
    Brand,
    Color,
    Size,
)


def _descendant_ids(root: Category) -> list[int]:
    """
    همهٔ آیدی‌های نوادگان (فرزند، نوه، …) + خود ریشه را برمی‌گرداند.
    بدون وابستگی به mptt. BFS ساده با تعداد کوئری کم.
    """
    ids = [root.id]
    frontier = [root.id]
    while frontier:
        children = list(
            Category.objects.filter(is_active=True, parent_id__in=frontier).values_list(
                "id", flat=True
            )
        )
        if not children:
            break
        ids.extend(children)
        frontier = children
    return ids


def _base_queryset():
    """
    Queryset پایه:
    - brand/category: select_related
    - images: prefetch مرتب‌شده (is_main اول)
    - min_price: ارزان‌ترین قیمت مؤثر بین واریانت‌ها
    """
    var_min_qs = (
        ProductVariation.objects.filter(product=OuterRef("pk"), is_active=True)
        .annotate(
            eff_price=Coalesce(
                F("price_override"),
                F("product__discount_price"),
                F("product__price"),
            )
        )
        .order_by("eff_price")
        .values("eff_price")[:1]
    )

    return (
        Product.objects.filter(is_active=True)
        .select_related("brand", "category")
        .prefetch_related(
            Prefetch(
                "images", queryset=ProductImage.objects.order_by("-is_main", "id")
            ),
        )
        .annotate(
            min_price=Coalesce(
                Subquery(
                    var_min_qs,
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),
                Coalesce(F("discount_price"), F("price")),
            )
        )
    )


def _apply_filters_sort(request, qs):
    """
    فیلترهای عمومی + مرتب‌سازی برای لیست‌ها/برند/دسته
    (با پشتیبانی از دستهٔ والد => شامل زیر‌دسته‌ها)
    """
    q = request.GET.get("q")
    if q:
        qs = qs.filter(
            Q(name__icontains=q)
            | Q(description__icontains=q)
            | Q(brand__name__icontains=q)
            | Q(category__name__icontains=q)
        )

    brand_slug = request.GET.get("brand")
    if brand_slug:
        qs = qs.filter(brand__slug=brand_slug)

    cat_slug = request.GET.get("cat")
    if cat_slug:
        cat_obj = get_object_or_404(Category, slug=cat_slug, is_active=True)
        qs = qs.filter(category_id__in=_descendant_ids(cat_obj))

    sort = (request.GET.get("sort") or "new").lower()
    order_map = {
        "new": ("-created_at", "-id"),
        "price_asc": ("min_price", "name", "id"),
        "price_desc": ("-min_price", "name", "id"),
        "name": ("name", "id"),
    }
    qs = qs.order_by(*order_map.get(sort, ("-created_at", "-id")))
    return qs, {"q": q, "brand": brand_slug, "cat": cat_slug, "sort": sort}


def product_list(request):
    """
    لیست محصولات با فیلتر و مرتب‌سازی (پوشش دستهٔ والد + زیر‌دسته‌ها)
    """
    qs = (
        Product.objects.filter(is_active=True)
        .select_related("brand", "category")
        .prefetch_related(
            Prefetch(
                "images", queryset=ProductImage.objects.order_by("-is_main", "id")
            ),
            Prefetch(
                "variations", queryset=ProductVariation.objects.filter(is_active=True)
            ),
        )
        .annotate(final_price=Coalesce(F("discount_price"), F("price")))
    )

    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(
            Q(name__icontains=q)
            | Q(description__icontains=q)
            | Q(brand__name__icontains=q)
        )

    brand = request.GET.get("brand")
    if brand:
        qs = qs.filter(brand__slug=brand)

    cat = request.GET.get("cat")
    if cat:
        cat_obj = get_object_or_404(Category, slug=cat, is_active=True)
        qs = qs.filter(category_id__in=_descendant_ids(cat_obj))

    color = request.GET.get("color")
    if color:
        qs = qs.filter(variations__color_id=color)

    size = request.GET.get("size")
    if size:
        qs = qs.filter(variations__size_id=size)

    min_price = request.GET.get("min")
    max_price = request.GET.get("max")
    if min_price:
        qs = qs.filter(final_price__gte=min_price)
    if max_price:
        qs = qs.filter(final_price__lte=max_price)

    in_stock = request.GET.get("in_stock")
    if in_stock == "1":
        qs = qs.filter(variations__stock__gt=0)

    sort = (request.GET.get("sort") or "new").lower()
    if sort == "price_asc":
        qs = qs.order_by("final_price", "-created_at")
    elif sort == "price_desc":
        qs = qs.order_by("-final_price", "-created_at")
    elif sort == "name":
        qs = qs.order_by("name", "id")
    else:  # newest
        qs = qs.order_by("-created_at", "-id")

    qs = qs.distinct()

    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    ctx = {
        "products": page_obj,
        "brands": Brand.objects.all().order_by("name"),
        "root_categories": (
            Category.objects.filter(is_active=True, parent__isnull=True)
            .prefetch_related("children")
            .order_by("name")
        ),
        "colors": Color.objects.all().order_by("name"),
        "sizes": Size.objects.all().order_by("sort_order", "name"),
        "q": q,
        "brand": brand,
        "cat": cat,
        "color": color,
        "size": size,
        "min_price": min_price,
        "max_price": max_price,
        "in_stock": in_stock,
        "sort": sort,
        "querystring": "&".join(
            f"{k}={v}" for k, v in request.GET.items() if k != "page"
        ),
    }
    return render(request, "products/product_list.html", ctx)


def category_detail(request, slug):
    """
    صفحهٔ دسته: محصولات دستهٔ انتخابی + تمام زیر‌دسته‌هایش
    """
    category = get_object_or_404(Category, slug=slug, is_active=True)
    qs = _base_queryset().filter(category_id__in=_descendant_ids(category))
    qs, params = _apply_filters_sort(request, qs)

    paginator = Paginator(qs, 12)
    products = paginator.get_page(request.GET.get("page"))

    categories = Category.objects.filter(
        parent__isnull=True, is_active=True
    ).prefetch_related("children")
    brands = Brand.objects.all()

    return render(
        request,
        "products/product_list.html",
        {
            "products": products,
            "query": params["q"],
            "active_brand": params["brand"],
            "active_category": category.slug,
            "active_sort": params["sort"],
            "categories": categories,
            "brands": brands,
        },
    )


def brand_detail(request, slug):
    brand = get_object_or_404(Brand, slug=slug)
    qs = _base_queryset().filter(brand=brand)
    qs, params = _apply_filters_sort(request, qs)

    paginator = Paginator(qs, 12)
    products = paginator.get_page(request.GET.get("page"))

    categories = Category.objects.filter(
        parent__isnull=True, is_active=True
    ).prefetch_related("children")
    brands = Brand.objects.all()

    return render(
        request,
        "products/product_list.html",
        {
            "products": products,
            "query": params["q"],
            "active_brand": brand.slug,
            "active_category": params["cat"],
            "active_sort": params["sort"],
            "categories": categories,
            "brands": brands,
        },
    )


def _norm_hex(val: str) -> str:
    """
    نرمال‌سازی مقدار HEX برای نمایش رنگ:
    - اگر None/خالی بود => رشتهٔ خالی
    - اگر # نداشت و طول 3 یا 6 بود => # اضافه می‌کنیم
    """
    if not val:
        return ""
    v = str(val).strip()
    if v and not v.startswith("#") and len(v) in (3, 6):
        v = "#" + v
    return v


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("brand", "category").prefetch_related(
            Prefetch(
                "images", queryset=ProductImage.objects.order_by("-is_main", "id")
            ),
            Prefetch(
                "variations",
                queryset=ProductVariation.objects.filter(is_active=True).select_related(
                    "color", "size"
                ),
            ),
        ),
        slug=slug,
        is_active=True,
    )

    variations = list(product.variations.all())
    colors, seen_colors = [], set()
    sizes, seen_sizes = [], set()
    variants = []

    for v in variations:
        variants.append(
            {
                "id": v.id,
                "color_id": v.color_id,
                "color": v.color.name if v.color else "",
                "color_code": (
                    getattr(v.color, "code", "") if v.color else ""
                ),  # انبارداری/داخلی
                "color_hex": (
                    _norm_hex(getattr(v.color, "hex_code", "")) if v.color else ""
                ),
                "size_id": v.size_id,
                "size": v.size.name if v.size else "",
                "price": str(v.final_price),
                "stock": v.stock,
                "image": (
                    v.image.url
                    if v.image
                    else (product.image.url if product.image else "")
                ),
                "sku": v.sku,
            }
        )

        if v.color_id and v.color_id not in seen_colors:
            colors.append(
                {
                    "id": v.color_id,
                    "name": v.color.name,
                    "hex": _norm_hex(getattr(v.color, "hex_code", "")) or "#eeeeee",
                }
            )
            seen_colors.add(v.color_id)

        if v.size_id and v.size_id not in seen_sizes:
            sizes.append({"id": v.size_id, "name": v.size.name})
            seen_sizes.add(v.size_id)

    return render(
        request,
        "products/product_detail.html",
        {
            "product": product,
            "variants": variants,  # شامل color_hex برای JS
            "colors": colors,  # هر رنگ با hex نرمال‌شده
            "sizes": sizes,
            "out_of_stock": request.GET.get("out_of_stock"),
            "available": request.GET.get("available"),
            "wanted": request.GET.get("wanted"),
            "vid": request.GET.get("vid"),
        },
    )
