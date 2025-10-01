from django.shortcuts import render
from django.db.models import Prefetch, Sum, Subquery, OuterRef, IntegerField, Value
from django.db.models.functions import Coalesce

from products.models import Product, ProductImage
from orders.models import OrderItem


def home(request):
    newest = (
        Product.objects.filter(is_active=True)
        .select_related("brand", "category")
        .prefetch_related(
            Prefetch("images", queryset=ProductImage.objects.order_by("-is_main", "id"))
        )
        .order_by("-created_at")[:12]
    )

    sales_sq = (
        OrderItem.objects.filter(variation__product=OuterRef("pk"))
        .values("variation__product")
        .annotate(total=Sum("quantity"))
        .values("total")[:1]
    )

    bestsellers = (
        Product.objects.filter(is_active=True)
        .select_related("brand", "category")
        .prefetch_related(
            Prefetch("images", queryset=ProductImage.objects.order_by("-is_main", "id"))
        )
        .annotate(
            sold=Coalesce(Subquery(sales_sq, output_field=IntegerField()), Value(0))
        )
        .order_by("-sold", "-created_at")[:12]
    )

    discounted = (
        Product.objects.filter(is_active=True, discount_price__isnull=False)
        .select_related("brand", "category")
        .prefetch_related(
            Prefetch("images", queryset=ProductImage.objects.order_by("-is_main", "id"))
        )
        .order_by("-updated_at", "-created_at")[:12]
    )

    return render(
        request,
        "home/index.html",
        {
            "newest": newest,
            "bestsellers": bestsellers,
            "discounted": discounted,
        },
    )


def about(request):
    return render(request, "home/about.html")
