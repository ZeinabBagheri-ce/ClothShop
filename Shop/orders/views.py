from decimal import Decimal
from django.db import transaction, models
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext as _

from cart.cart import Cart
from .forms import CheckoutForm
from .models import Order, OrderItem, Coupon
from .utils import calc_shipping
from accounts.forms import AddressForm
from accounts.models import Address


@login_required
@transaction.atomic
def checkout(request):
    """
    مرحله آدرس (در صورت نداشتن آدرس) + مرور و ثبت سفارش.
    """
    cart = Cart(request)
    if cart.total_quantity() == 0:
        messages.info(request, _("سبد شما خالی است."))
        return redirect("cart:detail")

    user_addresses = Address.objects.filter(user=request.user)
    has_addresses = user_addresses.exists()

    # اگر آدرسی ندارد، اول باید آدرس بسازد
    step = request.GET.get("step") or ("address" if not has_addresses else "review")

    # ---------- مرحله ساخت آدرس ----------
    if step == "address":
        if request.method == "POST":
            addr_form = AddressForm(request.POST, prefix="addr_new")
            if addr_form.is_valid():
                address = addr_form.save(commit=False)
                address.user = request.user
                if not has_addresses:
                    address.is_default = True
                address.save()
                messages.success(request, _("آدرس با موفقیت ذخیره شد."))
                return redirect(f"{request.path}?step=review")
            messages.error(request, _("لطفاً خطاهای فرم آدرس را بررسی کنید."))
        else:
            addr_form = AddressForm(prefix="addr_new")

        return render(
            request,
            "orders/checkout.html",
            {
                "step": "address",
                "addr_form": addr_form,
                "has_addresses": has_addresses,
                "cart": cart,
            },
        )

    # ---------- مرحله مرور و ثبت ----------
    if request.method == "POST":
        form = CheckoutForm(request.user, request.POST)
        if form.is_valid():
            address = form.cleaned_data.get("address_id")
            if not address:
                messages.error(
                    request, _("لطفاً یک آدرس انتخاب کنید یا از مرحله قبل آدرس بسازید.")
                )
                return render(
                    request,
                    "orders/checkout.html",
                    {
                        "step": "review",
                        "form": form,
                        "cart": cart,
                        "has_addresses": has_addresses,
                    },
                )

            subtotal = cart.total_price()

            # کد تخفیف
            coupon_code = (form.cleaned_data.get("coupon_code") or "").strip()
            discount_amount = Decimal("0")
            applied_code = ""
            coupon_obj = None
            if coupon_code:
                coupon_obj = Coupon.objects.filter(code__iexact=coupon_code).first()
                if not coupon_obj or not coupon_obj.is_valid_now():
                    messages.error(request, _("کد تخفیف معتبر نیست."))
                else:
                    discount_amount = Decimal(coupon_obj.compute_discount(subtotal))
                    applied_code = coupon_obj.code

            # هزینه ارسال
            shipping_cost = calc_shipping(subtotal - discount_amount, address.province.name)

            total = subtotal - discount_amount + shipping_cost
            if total < 0:
                total = Decimal("0")

            # ساخت سفارش
            order = Order.objects.create(
                user=request.user,
                full_name=address.full_name,
                phone=address.phone,
                province=address.province.name,
                city=address.city.name,
                address_exact=address.address_exact,
                postal_code=address.postal_code,
                note=form.cleaned_data.get("note", ""),
                subtotal=subtotal,
                discount_amount=discount_amount,
                shipping_cost=shipping_cost,
                total=total,
                coupon_code=applied_code,
            )

            # آیتم‌ها + کاهش موجودی
            for row in cart:
                v = row["variation"]
                qty = row["quantity"]

                if v.stock < qty:
                    messages.error(request, _(f"موجودی کافی برای {v.product.name} موجود نیست."))
                    raise ValueError("Insufficient stock")

                OrderItem.objects.create(
                    order=order,
                    variation=v,
                    product_name=v.product.name,
                    sku=v.sku,
                    price=row["price"],
                    quantity=qty,
                    line_total=row["total"],
                )
                v.stock -= qty
                v.save(update_fields=["stock"])

            # افزایش دفعات استفاده از کوپن
            if coupon_obj and applied_code:
                Coupon.objects.filter(pk=coupon_obj.pk).update(
                    used_count=models.F("used_count") + 1
                )

            # پاکسازی سبد
            cart.clear()
            messages.success(request, _("سفارش شما ثبت شد."))

            # هدایت به صفحه موفقیت؛ اگر درگاه داری می‌تونی این‌جا به درگاه هم هدایت کنی
            return redirect("orders:success", order_id=order.id)
        else:
            messages.error(request, _("لطفاً خطاهای فرم را بررسی کنید."))
    else:
        form = CheckoutForm(request.user)

    return render(
        request,
        "orders/checkout.html",
        {
            "step": "review",
            "form": form,
            "cart": cart,
            "has_addresses": has_addresses,
        },
    )


@login_required
def order_success(request, order_id: int):
    """
    نمایش صفحه موفقیت ثبت/پرداخت سفارش.
    - کاربر عادی فقط سفارش خودش را می‌بیند.
    - کارکنان (staff) می‌توانند هر سفارشی را ببینند.
    """
    if request.user.is_staff:
        order = get_object_or_404(Order, id=order_id)
    else:
        order = get_object_or_404(Order, id=order_id, user=request.user)

    return render(request, "orders/success.html", {"order": order})


@login_required
def payment_failed(request, order_id: int | None = None):
    """
    نمایش صفحهٔ خطا/لغو پرداخت (مثلاً بازگشت از درگاه).
    - اگر order_id ارسال شود و کاربر دسترسی داشته باشد، خلاصه سفارش نیز نشان داده می‌شود.
    """
    order = None
    if order_id is not None:
        if request.user.is_staff:
            order = get_object_or_404(Order, id=order_id)
        else:
            order = get_object_or_404(Order, id=order_id, user=request.user)

    messages.error(request, _("پرداخت ناموفق بود یا توسط کاربر لغو شد."))
    return render(request, "orders/payment_failed.html", {"order": order})
