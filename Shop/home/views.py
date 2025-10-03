from django.shortcuts import render
from django.db.models import Prefetch, Sum
from django.utils import timezone
from datetime import timedelta
from products.models import Product, ProductImage

def home(request):
    # جدیدترین‌ها
    newest = (
        Product.objects.filter(is_active=True)
        .select_related("brand", "category")
        .prefetch_related(
            Prefetch("images", queryset=ProductImage.objects.order_by("-is_main", "id"))
        )
        .order_by("-created_at")[:12]
    )

    # تخفیف‌دارها
    discounted = (
        Product.objects.filter(is_active=True, discount_price__isnull=False)
        .select_related("brand", "category")
        .prefetch_related(
            Prefetch("images", queryset=ProductImage.objects.order_by("-is_main", "id"))
        )
        .order_by("-updated_at", "-created_at")[:12]
    )

    # پرفروش‌ترین‌ها در 90 روز گذشته
    cutoff = timezone.now() - timedelta(days=90)
    valid_statuses = ["PAID", "PROCESSING", "SHIPPED", "DELIVERED"]

    try:
        bestsellers = (
            Product.objects.filter(
                is_active=True,
                variations__orderitem__order__created_at__gte=cutoff,
                variations__orderitem__order__status__in=valid_statuses,
            )
            .select_related("brand", "category")
            .prefetch_related(
                Prefetch("images", queryset=ProductImage.objects.order_by("-is_main", "id"))
            )
            .annotate(sold_qty=Sum("variations__orderitem__quantity"))
            .order_by("-sold_qty", "-created_at")[:12]
        )
    except Exception:
        # اگر اپ orders یا روابط موجود نباشه، جدیدترین‌ها رو نشون بده
        bestsellers = newest

    return render(
        request,
        "home/index.html",
        {
            "newest": newest,
            "discounted": discounted,
            "bestsellers": bestsellers,
        },
    )


def about(request):
    return render(request, "home/about.html")
