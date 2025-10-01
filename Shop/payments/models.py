from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from orders.models import Order

class Payment(models.Model):
    class Status(models.TextChoices):
        INIT = "init", _("ایجاد شده")
        STARTED = "started", _("ارسال به درگاه")
        SUCCESS = "success", _("موفق")
        FAILED = "failed", _("ناموفق")

    order = models.OneToOneField(Order, on_delete=models.PROTECT, related_name="payment", verbose_name=_("سفارش"))
    user  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(_("مبلغ"), max_digits=12, decimal_places=2)

    status = models.CharField(_("وضعیت"), max_length=16, choices=Status.choices, default=Status.INIT)
    authority = models.CharField(_("شناسه درگاه/Authority"), max_length=64, blank=True)  # در شبیه‌ساز اختیاری
    ref_id    = models.CharField(_("کد پیگیری"), max_length=64, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    paid_at    = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payment #{self.id} for Order #{self.order_id} — {self.get_status_display()}"
