
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("products", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Order",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "در انتظار پرداخت"),
                            ("paid", "پرداخت شده"),
                            ("canceled", "لغو شده"),
                            ("shipped", "ارسال شده"),
                        ],
                        default="pending",
                        max_length=16,
                        verbose_name="وضعیت",
                    ),
                ),
                (
                    "full_name",
                    models.CharField(
                        max_length=100, verbose_name="نام و نام\u200cخانوادگی"
                    ),
                ),
                (
                    "phone",
                    models.CharField(blank=True, max_length=20, verbose_name="تلفن"),
                ),
                ("province", models.CharField(max_length=100, verbose_name="استان")),
                ("city", models.CharField(max_length=100, verbose_name="شهر")),
                (
                    "address_exact",
                    models.CharField(max_length=255, verbose_name="آدرس دقیق"),
                ),
                (
                    "postal_code",
                    models.CharField(blank=True, max_length=20, verbose_name="کد پستی"),
                ),
                ("note", models.TextField(blank=True, verbose_name="توضیحات سفارش")),
                (
                    "subtotal",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                        verbose_name="جمع جزء",
                    ),
                ),
                (
                    "shipping_cost",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                        verbose_name="هزینه ارسال",
                    ),
                ),
                (
                    "total",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                        verbose_name="مبلغ نهایی",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="تاریخ ایجاد"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="orders",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="کاربر",
                    ),
                ),
            ],
            options={
                "verbose_name": "سفارش",
                "verbose_name_plural": "سفارش\u200cها",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "product_name",
                    models.CharField(max_length=200, verbose_name="نام محصول"),
                ),
                ("sku", models.CharField(max_length=40, verbose_name="SKU")),
                (
                    "price",
                    models.DecimalField(
                        decimal_places=2, max_digits=12, verbose_name="قیمت واحد"
                    ),
                ),
                (
                    "quantity",
                    models.PositiveIntegerField(default=1, verbose_name="تعداد"),
                ),
                (
                    "line_total",
                    models.DecimalField(
                        decimal_places=2, max_digits=12, verbose_name="جمع خط"
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="orders.order",
                    ),
                ),
                (
                    "variation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="products.productvariation",
                    ),
                ),
            ],
        ),
    ]
