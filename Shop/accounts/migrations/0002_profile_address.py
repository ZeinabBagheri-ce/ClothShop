
import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Profile",
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
                    "phone",
                    models.CharField(
                        blank=True,
                        help_text="مثال: +989123456789",
                        max_length=20,
                        null=True,
                        unique=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                "^\\+?[1-9]\\d{7,14}$",
                                "شماره را در قالب بین\u200cالمللی وارد کنید",
                            )
                        ],
                        verbose_name="شماره موبایل",
                    ),
                ),
                (
                    "is_phone_verified",
                    models.BooleanField(default=False, verbose_name="تأیید تلفن"),
                ),
                (
                    "avatar",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to="avatars/%Y/%m/",
                        verbose_name="تصویر پروفایل",
                    ),
                ),
                (
                    "date_of_birth",
                    models.DateField(blank=True, null=True, verbose_name="تاریخ تولد"),
                ),
                (
                    "newsletter_opt_in",
                    models.BooleanField(default=False, verbose_name="اشتراک خبرنامه"),
                ),
                (
                    "marketing_opt_in",
                    models.BooleanField(
                        default=False, verbose_name="اجازه ارسال پیشنهادات"
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Address",
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
                    "type",
                    models.CharField(
                        choices=[("shipping", "حمل و نقل"), ("billing", "صورتحساب")],
                        default="shipping",
                        max_length=20,
                        verbose_name="نوع",
                    ),
                ),
                (
                    "full_name",
                    models.CharField(max_length=100, verbose_name="نام و نام خانوادگی"),
                ),
                (
                    "phone",
                    models.CharField(
                        blank=True, max_length=20, verbose_name="شماره تلفن"
                    ),
                ),
                ("line1", models.CharField(max_length=255, verbose_name="آدرس ۱")),
                (
                    "line2",
                    models.CharField(blank=True, max_length=255, verbose_name="آدرس ۲"),
                ),
                ("city", models.CharField(max_length=100, verbose_name="شهر")),
                (
                    "state",
                    models.CharField(blank=True, max_length=100, verbose_name="استان"),
                ),
                (
                    "postal_code",
                    models.CharField(max_length=20, verbose_name="کد پستی"),
                ),
                (
                    "country",
                    models.CharField(
                        help_text="کد کشور دوحرفی ISO مثل IR, TR, DE",
                        max_length=2,
                        verbose_name="کشور",
                    ),
                ),
                (
                    "is_default",
                    models.BooleanField(
                        default=False, verbose_name="آدرس پیش\u200cفرض"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="addresses",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "آدرس",
                "verbose_name_plural": "آدرس\u200cها",
                "indexes": [
                    models.Index(
                        fields=["user", "type", "is_default"],
                        name="accounts_ad_user_id_b03917_idx",
                    ),
                    models.Index(
                        fields=["country", "postal_code"],
                        name="accounts_ad_country_ffef06_idx",
                    ),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        condition=models.Q(("is_default", True)),
                        fields=("user", "type"),
                        name="unique_default_address_per_type",
                    )
                ],
            },
        ),
    ]
