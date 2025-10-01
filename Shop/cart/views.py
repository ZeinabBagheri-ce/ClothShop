from urllib.parse import urlencode

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils.translation import gettext as _

from .cart import Cart
from .forms import AddToCartForm
from products.models import ProductVariation


@require_POST
def add_to_cart(request):
    """
    اگر تعداد درخواستی > موجودی باشد، به صفحه محصول ریدایرکت می‌کنیم و
    پارامترهای لازم را برای نمایش هشدار در همان صفحه می‌فرستیم.
    """
    form = AddToCartForm(request.POST)
    if not form.is_valid():
        messages.error(request, _("اطلاعات نامعتبر سبد خرید."))
        return redirect(request.META.get("HTTP_REFERER", "/"))

    variation = get_object_or_404(
        ProductVariation, id=form.cleaned_data["variation_id"], is_active=True
    )
    qty = form.cleaned_data["quantity"]

    if variation.stock < qty:
        params = urlencode(
            {
                "out_of_stock": 1,
                "available": variation.stock,
                "wanted": qty,
                "vid": variation.id,  # تا روی همان واریانت فوکوس شود
            }
        )
        return redirect(f"{variation.product.get_absolute_url()}?{params}")

    cart = Cart(request)
    cart.add(variation.id, quantity=qty)
    messages.success(request, _("به سبد اضافه شد."))
    return redirect("cart:detail")


def remove_from_cart(request, variation_id: int):
    cart = Cart(request)
    cart.remove(variation_id)
    messages.info(request, _("از سبد حذف شد."))
    return redirect("cart:detail")


def update_cart(request, variation_id: int):
    """
    به‌روزرسانی تعداد یک آیتم. اگر تعداد جدید از موجودی بیشتر باشد،
    مشابه اضافه‌کردن، کاربر را به صفحه محصول برمی‌گردانیم تا پیام را همان‌جا ببیند.
    """
    cart = Cart(request)
    try:
        qty = int(request.POST.get("quantity", 1))
    except ValueError:
        qty = 1

    variation = get_object_or_404(ProductVariation, pk=variation_id, is_active=True)
    if qty > variation.stock:
        params = urlencode(
            {
                "out_of_stock": 1,
                "available": variation.stock,
                "wanted": qty,
                "vid": variation.id,
            }
        )
        return redirect(f"{variation.product.get_absolute_url()}?{params}")

    cart.add(variation_id, quantity=qty, replace=True)
    messages.success(request, _("سبد به‌روزرسانی شد."))
    return redirect("cart:detail")


def cart_detail(request):
    cart = Cart(request)
    return render(request, "cart/cart_detail.html", {"cart": cart})
