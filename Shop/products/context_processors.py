from django.db.models import Prefetch
from .models import Category


def nav_categories(request):
    """
    ریشه‌ها + یک‌سطح فرزندان برای منوی ناوبار.
    خروجی همزمان با دو کلید برمی‌گردد تا:
      - nav_categories برای تمپلیت‌های جدید
      - top_categories برای سازگاری با کدهای قدیمی
    """
    roots = (
        Category.objects.filter(is_active=True, parent__isnull=True)
        .prefetch_related(
            Prefetch(
                "children",
                queryset=Category.objects.filter(is_active=True).order_by("name"),
            )
        )
        .order_by("name")
    )
    return {"nav_categories": roots, "top_categories": roots}


top_categories = nav_categories
