from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.urls import reverse


def unique_slugify(
    instance,
    value,
    field_name: str = "slug",
    allow_unicode: bool = True,
    max_length: int = 160,
):

    base = slugify(value, allow_unicode=allow_unicode) or "item"
    field = instance._meta.get_field(field_name)
    max_len = getattr(field, "max_length", max_length) or max_length
    base = base[:max_len]

    slug = base
    Model = instance.__class__
    qs = Model._default_manager.all()
    if instance.pk:
        qs = qs.exclude(pk=instance.pk)

    i = 2
    while qs.filter(**{field_name: slug}).exists():
        suffix = f"-{i}"
        slug = (base[: max_len - len(suffix)]) + suffix
        i += 1
    return slug


class Category(models.Model):
    name = models.CharField(_("نام دسته"), max_length=100)
    slug = models.SlugField(_("اسلاگ"), unique=True, allow_unicode=True, max_length=120)
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children", on_delete=models.CASCADE
    )
    is_active = models.BooleanField(_("فعال"), default=True)

    class Meta:
        verbose_name = _("دسته")
        verbose_name_plural = _("دسته‌ها")
        ordering = ["name"]
        indexes = [models.Index(fields=["slug"])]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(
                self, self.name, allow_unicode=True, max_length=120
            )
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("products:category", args=[self.slug])


class Brand(models.Model):
    name = models.CharField(_("نام برند"), max_length=100, unique=True)
    slug = models.SlugField(_("اسلاگ"), unique=True, allow_unicode=True, max_length=120)

    class Meta:
        verbose_name = _("برند")
        verbose_name_plural = _("برندها")
        ordering = ["name"]
        indexes = [models.Index(fields=["slug"])]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(
                self, self.name, allow_unicode=True, max_length=120
            )
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("products:brand", args=[self.slug])


class Color(models.Model):
    name = models.CharField(_("رنگ"), max_length=50)

    hex_code = models.CharField(
        _("کد HEX (اختیاری)"), max_length=7, blank=True, help_text=_("مثال: #000000")
    )

    code = models.CharField(
        _("کد یکتای رنگ"),
        max_length=32,
        blank=True,
        null=True,
        help_text=_("مثل: RED, BLK, CRM …"),
    )

    class Meta:
        verbose_name = _("رنگ")
        verbose_name_plural = _("رنگ‌ها")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Size(models.Model):
    name = models.CharField(_("سایز"), max_length=20)
    sort_order = models.PositiveIntegerField(_("ترتیب"), default=0)
    code = models.CharField(
        _("کد یکتای سایز"),
        max_length=32,
        blank=True,
        null=True,
        help_text=_("مثل: S, M, L, 38, 40 …"),
    )

    class Meta:
        verbose_name = _("سایز")
        verbose_name_plural = _("سایزها")
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category, related_name="products", on_delete=models.PROTECT
    )
    brand = models.ForeignKey(Brand, related_name="products", on_delete=models.PROTECT)

    name = models.CharField(_("نام محصول"), max_length=200)
    slug = models.SlugField(_("اسلاگ"), unique=True, allow_unicode=True, max_length=160)

    description = models.TextField(_("توضیحات"), blank=True)

    price = models.DecimalField(_("قیمت پایه"), max_digits=12, decimal_places=2)
    discount_price = models.DecimalField(
        _("قیمت با تخفیف"),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("اگر خالی بماند همان قیمت پایه لحاظ می‌شود"),
    )

    is_active = models.BooleanField(_("فعال"), default=True)
    created_at = models.DateTimeField(_("ساخته‌شده"), auto_now_add=True)
    updated_at = models.DateTimeField(_("به‌روزرسانی"), auto_now=True)

    image = models.ImageField(
        _("تصویر اصلی"), upload_to="products/%Y/%m/", null=True, blank=True
    )

    class Meta:
        verbose_name = _("محصول")
        verbose_name_plural = _("محصولات")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["brand"]),
            models.Index(fields=["category"]),
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        if self.discount_price is not None and self.discount_price >= self.price:
            raise ValidationError(
                {"discount_price": _("قیمت با تخفیف باید کمتر از قیمت پایه باشد.")}
            )

    @property
    def base_final_price(self):
        return self.discount_price or self.price

    def stock_total(self) -> int:
        return sum(self.variations.values_list("stock", flat=True))

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(
                self, self.name, allow_unicode=True, max_length=160
            )
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("products:detail", args=[self.slug])


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, related_name="images", on_delete=models.CASCADE
    )
    image = models.ImageField(_("تصویر"), upload_to="products/gallery/%Y/%m/")
    alt_text = models.CharField(_("متن جایگزین"), max_length=150, blank=True)
    is_main = models.BooleanField(_("تصویر اصلی؟"), default=False)

    class Meta:
        verbose_name = _("تصویر محصول")
        verbose_name_plural = _("تصاویر محصول")
        ordering = ["-is_main"]

    def __str__(self):
        return f"تصویر {self.product.name}"


class ProductVariation(models.Model):
    product = models.ForeignKey(
        Product, related_name="variations", on_delete=models.CASCADE
    )

    color = models.ForeignKey(
        Color,
        related_name="variations",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    size = models.ForeignKey(
        Size, related_name="variations", on_delete=models.PROTECT, null=True, blank=True
    )

    sku = models.CharField(
        _("SKU"), max_length=40, unique=True, help_text=_("کد یکتا برای انبار/فروش")
    )
    barcode = models.CharField(_("بارکد"), max_length=64, blank=True)

    price_override = models.DecimalField(
        _("قیمت اختصاصی"),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("اگر خالی باشد از قیمت محصول استفاده می‌شود"),
    )
    stock = models.PositiveIntegerField(_("موجودی"), default=0)
    is_active = models.BooleanField(_("فعال"), default=True)
    image = models.ImageField(
        _("تصویر واریانت (اختیاری)"),
        upload_to="products/variants/%Y/%m/",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("واریانت محصول")
        verbose_name_plural = _("واریانت‌های محصول")
        ordering = ["product", "color__name", "size__sort_order", "size__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "color", "size"],
                name="unique_variation_per_product_color_size",
            ),
        ]
        indexes = [
            models.Index(fields=["product", "is_active"]),
            models.Index(fields=["color"]),
            models.Index(fields=["size"]),
        ]

    def __str__(self):
        parts = []
        if self.color:
            parts.append(self.color.name)
        if self.size:
            parts.append(self.size.name)
        suffix = " / ".join(parts) if parts else "بدون ویژگی"
        return f"{self.product.name} — {suffix}"

    @property
    def final_price(self):
        return self.price_override or self.product.base_final_price
