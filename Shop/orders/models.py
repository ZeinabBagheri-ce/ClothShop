from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from products.models import ProductVariation


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("در انتظار پرداخت")
        PAID = "paid", _("پرداخت شده")
        CANCELED = "canceled", _("لغو شده")
        SHIPPED = "shipped", _("ارسال شده")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name=_("کاربر"),
    )
    status = models.CharField(
        _("وضعیت"), max_length=16, choices=Status.choices, default=Status.PENDING
    )

    full_name = models.CharField(_("نام و نام‌خانوادگی"), max_length=100)
    phone = models.CharField(_("تلفن"), max_length=20, blank=True)
    province = models.CharField(_("استان"), max_length=100)
    city = models.CharField(_("شهر"), max_length=100)
    address_exact = models.CharField(_("آدرس دقیق"), max_length=255)
    postal_code = models.CharField(_("کد پستی"), max_length=20, blank=True)

    note = models.TextField(_("توضیحات سفارش"), blank=True)

    subtotal = models.DecimalField(
        _("جمع جزء"), max_digits=12, decimal_places=2, default=0
    )
    shipping_cost = models.DecimalField(
        _("هزینه ارسال"), max_digits=12, decimal_places=2, default=0
    )
    total = models.DecimalField(
        _("مبلغ نهایی"), max_digits=12, decimal_places=2, default=0
    )

    created_at = models.DateTimeField(_("تاریخ ایجاد"), default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("سفارش")
        verbose_name_plural = _("سفارش‌ها")

    def __str__(self):
        return f"Order #{self.id} - {self.get_status_display()}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    variation = models.ForeignKey(
        ProductVariation, on_delete=models.PROTECT, related_name="+"
    )
    product_name = models.CharField(_("نام محصول"), max_length=200)  # snapshot
    sku = models.CharField(_("SKU"), max_length=40)
    price = models.DecimalField(_("قیمت واحد"), max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(_("تعداد"), default=1)
    line_total = models.DecimalField(_("جمع خط"), max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"


class Coupon(models.Model):
    code = models.CharField(_("کد"), max_length=40, unique=True)
    percent_off = models.PositiveIntegerField(_("درصد تخفیف"), null=True, blank=True)
    amount_off = models.DecimalField(
        _("تخفیف مبلغی"), max_digits=12, decimal_places=2, null=True, blank=True
    )
    is_active = models.BooleanField(_("فعال"), default=True)
    starts_at = models.DateTimeField(_("شروع"), null=True, blank=True)
    ends_at = models.DateTimeField(_("پایان"), null=True, blank=True)
    usage_limit = models.PositiveIntegerField(
        _("حداکثر دفعات مصرف"), null=True, blank=True
    )
    used_count = models.PositiveIntegerField(_("دفعات مصرف شده"), default=0)
    min_subtotal = models.DecimalField(
        _("حداقل جمع جزء"), max_digits=12, decimal_places=2, null=True, blank=True
    )

    class Meta:
        verbose_name = _("کوپن")
        verbose_name_plural = _("کوپن‌ها")
        ordering = ["-id"]

    def __str__(self):
        return self.code

    def is_valid_now(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.starts_at and now < self.starts_at:
            return False
        if self.ends_at and now > self.ends_at:
            return False
        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            return False
        return True

    def compute_discount(self, subtotal):
        if self.min_subtotal and subtotal < self.min_subtotal:
            return 0
        discount = 0
        if self.percent_off:
            discount += (subtotal * self.percent_off) / 100
        if self.amount_off:
            discount += self.amount_off
        return min(discount, subtotal)


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("در انتظار پرداخت")
        PAID = "paid", _("پرداخت شده")
        CANCELED = "canceled", _("لغو شده")
        SHIPPED = "shipped", _("ارسال شده")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name=_("کاربر"),
    )
    status = models.CharField(
        _("وضعیت"), max_length=16, choices=Status.choices, default=Status.PENDING
    )

    full_name = models.CharField(_("نام و نام‌خانوادگی"), max_length=100)
    phone = models.CharField(_("تلفن"), max_length=20, blank=True)
    province = models.CharField(_("استان"), max_length=100)
    city = models.CharField(_("شهر"), max_length=100)
    address_exact = models.CharField(_("آدرس دقیق"), max_length=255)
    postal_code = models.CharField(_("کد پستی"), max_length=20, blank=True)

    note = models.TextField(_("توضیحات سفارش"), blank=True)

    subtotal = models.DecimalField(
        _("جمع جزء"), max_digits=12, decimal_places=2, default=0
    )
    discount_amount = models.DecimalField(
        _("تخفیف"), max_digits=12, decimal_places=2, default=0
    )
    shipping_cost = models.DecimalField(
        _("هزینه ارسال"), max_digits=12, decimal_places=2, default=0
    )
    total = models.DecimalField(
        _("مبلغ نهایی"), max_digits=12, decimal_places=2, default=0
    )
    coupon_code = models.CharField(_("کد کوپن"), max_length=40, blank=True)

    created_at = models.DateTimeField(_("تاریخ ایجاد"), default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("سفارش")
        verbose_name_plural = _("سفارش‌ها")

    def __str__(self):
        return f"Order #{self.id} - {self.get_status_display()}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    variation = models.ForeignKey(
        ProductVariation, on_delete=models.PROTECT, related_name="+"
    )
    product_name = models.CharField(_("نام محصول"), max_length=200)
    sku = models.CharField(_("SKU"), max_length=40)
    price = models.DecimalField(_("قیمت واحد"), max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(_("تعداد"), default=1)
    line_total = models.DecimalField(_("جمع خط"), max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"
