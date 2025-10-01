
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Coupon",
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
                    "code",
                    models.CharField(max_length=40, unique=True, verbose_name="کد"),
                ),
                (
                    "percent_off",
                    models.PositiveIntegerField(
                        blank=True, null=True, verbose_name="درصد تخفیف"
                    ),
                ),
                (
                    "amount_off",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=12,
                        null=True,
                        verbose_name="تخفیف مبلغی",
                    ),
                ),
                ("is_active", models.BooleanField(default=True, verbose_name="فعال")),
                (
                    "starts_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="شروع"),
                ),
                (
                    "ends_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="پایان"),
                ),
                (
                    "usage_limit",
                    models.PositiveIntegerField(
                        blank=True, null=True, verbose_name="حداکثر دفعات مصرف"
                    ),
                ),
                (
                    "used_count",
                    models.PositiveIntegerField(
                        default=0, verbose_name="دفعات مصرف شده"
                    ),
                ),
                (
                    "min_subtotal",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=12,
                        null=True,
                        verbose_name="حداقل جمع جزء",
                    ),
                ),
            ],
            options={
                "verbose_name": "کوپن",
                "verbose_name_plural": "کوپن\u200cها",
                "ordering": ["-id"],
            },
        ),
        migrations.AddField(
            model_name="order",
            name="coupon_code",
            field=models.CharField(blank=True, max_length=40, verbose_name="کد کوپن"),
        ),
        migrations.AddField(
            model_name="order",
            name="discount_amount",
            field=models.DecimalField(
                decimal_places=2, default=0, max_digits=12, verbose_name="تخفیف"
            ),
        ),
    ]
