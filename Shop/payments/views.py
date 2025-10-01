import requests
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.decorators import login_required

from orders.models import Order
from .models import Payment


def _to_rial(amount_decimal: Decimal) -> int:

    return int(Decimal(amount_decimal) * 10)


@login_required
@transaction.atomic
def zarinpal_start(request, order_id: int):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.total <= 0:
        messages.info(request, "مبلغ سفارش صفر است.")
        return redirect("orders:success", order_id=order.id)

    if hasattr(order, "payment") and order.payment.status == Payment.Status.SUCCESS:
        messages.info(request, "این سفارش قبلاً پرداخت شده است.")
        return redirect("orders:success", order_id=order.id)

    payment, _ = Payment.objects.get_or_create(
        order=order, defaults={"user": request.user, "amount": order.total}
    )
    payment.amount = order.total
    payment.status = Payment.Status.STARTED
    payment.save()

    data = {
        "MerchantID": settings.ZARINPAL_MERCHANT_ID,
        "Amount": _to_rial(
            order.total
        ),  # اگر قیمت‌ها ریال هستند، همین order.total را int کن
        "Description": f"Order #{order.id}",
        "CallbackURL": settings.ZARINPAL_CALLBACK_URL,
        "Email": request.user.email or "",
    }
    headers = {"accept": "application/json", "content-type": "application/json"}

    try:
        resp = requests.post(
            settings.ZARINPAL_REQUEST_URL, json=data, headers=headers, timeout=15
        )
        payload = resp.json()
    except Exception as e:
        messages.error(request, f"خطا در اتصال به زرین‌پال: {e}")
        return redirect("orders:success", order_id=order.id)

    if payload.get("Status") == 100:
        authority = payload["Authority"]
        payment.authority = authority
        payment.save(update_fields=["authority"])
        return redirect(f"{settings.ZARINPAL_GATEWAY_URL}{authority}")

    messages.error(request, f"خطای زرین‌پال (PaymentRequest): {payload.get('Status')}")
    return redirect("orders:success", order_id=order.id)


@login_required
@transaction.atomic
def zarinpal_callback(request):
    authority = request.GET.get("Authority")
    status = request.GET.get("Status")
    payment = get_object_or_404(Payment, authority=authority, user=request.user)
    order = payment.order

    if status != "OK":
        payment.status = Payment.Status.FAILED
        payment.save(update_fields=["status"])
        messages.error(request, "پرداخت لغو شد یا ناموفق بود.")
        return redirect("orders:success", order_id=order.id)

    data = {
        "MerchantID": settings.ZARINPAL_MERCHANT_ID,
        "Amount": _to_rial(payment.amount),
        "Authority": authority,
    }
    headers = {"accept": "application/json", "content-type": "application/json"}

    try:
        resp = requests.post(
            settings.ZARINPAL_VERIFY_URL, json=data, headers=headers, timeout=15
        )
        payload = resp.json()
    except Exception as e:
        messages.error(request, f"خطا در ارتباط با زرین‌پال (Verify): {e}")
        return redirect("orders:success", order_id=order.id)

    if payload.get("Status") == 100:
        payment.status = Payment.Status.SUCCESS
        payment.ref_id = str(payload.get("RefID"))
        payment.paid_at = timezone.now()
        payment.save(update_fields=["status", "ref_id", "paid_at"])

        order.status = order.Status.PAID
        order.save(update_fields=["status"])

        messages.success(request, f"پرداخت موفق بود. کد پیگیری: {payment.ref_id}")
    else:
        payment.status = Payment.Status.FAILED
        payment.save(update_fields=["status"])
        messages.error(request, f"پرداخت ناموفق. کد وضعیت: {payload.get('Status')}")

    return redirect("orders:success", order_id=order.id)
