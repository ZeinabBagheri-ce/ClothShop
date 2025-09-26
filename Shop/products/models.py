from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify


# -------------------- Category (درختی) --------------------
class Category(models.Model):
    name = models.CharField(_("نام دسته"), max_length=100)
    slug = models.SlugField(_("اسلاگ"), unique=True, allow_unicode=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True,
        related_name="children",
        on_delete=models.CASCADE
    )
    is_active = models.BooleanField(_("فعال"), default=True)

    class Meta:
        verbose_name = _("دسته")
        verbose_name_plural = _("دسته‌ها")
        ordering = ["name"]

    def __str__(self):
        return self.name


# -------------------- Brand --------------------
class Brand(models.Model):
    name = models.CharField(_("نام برند"), max_length=100, unique=True)
    slug = models.SlugField(_("اسلاگ"), unique=True, allow_unicode=True)

    class Meta:
        verbose_name = _("برند")
        verbose_name_plural = _("برندها")
        ordering = ["name"]

    def __str__(self):
        return self.name


# -------------------- Color / Size (ویژگی‌های قابل انتخاب) --------------------
class Color(models.Model):
    name = models.CharField(_("رنگ"), max_length=50, unique=True)
    code = models.CharField(
        _("کد رنگ (اختیاری، HEX)"),
        max_length=7, blank=True,
        help_text=_("مثال: #000000")
    )

    class Meta:
        verbose_name = _("رنگ")
        verbose_name_plural = _("رنگ‌ها")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Size(models.Model):
    name = models.CharField(_("سایز"), max_length=20, unique=True)
    sort_order = models.PositiveIntegerField(_("ترتیب"), default=0)

    class Meta:
        verbose_name = _("سایز")
        verbose_name_plural = _("سایزها")
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


# -------------------- Product --------------------
class Product(models.Model):
    category = models.ForeignKey(Category, related_name="products", on_delete=models.PROTECT)
    brand = models.ForeignKey(Brand, related_name="products", on_delete=models.PROTECT)

    name = models.CharField(_("نام محصول"), max_length=200)
    slug = models.SlugField(_("اسلاگ"), unique=True, allow_unicode=True)

    description = models.TextField(_("توضیحات"), blank=True)

    price = models.DecimalField(_("قیمت پایه"), max_digits=12, decimal_places=2)
    discount_price = models.DecimalField(_("قیمت با تخفیف"), max_digits=12, decimal_places=2,
                                         null=True, blank=True,
                                         help_text=_("اگر خالی بماند همان قیمت پایه لحاظ می‌شود"))

    is_active = models.BooleanField(_("فعال"), default=True)
    created_at = models.DateTimeField(_("ساخته‌شده"), auto_now_add=True)
    updated_at = models.DateTimeField(_("به‌روزرسانی"), auto_now=True)

    image = models.ImageField(_("تصویر اصلی"), upload_to="products/%Y/%m/", null=True, blank=True)

    class Meta:
        verbose_name = _("محصول")
        verbose_name_plural = _("محصولات")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["brand"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return self.name

    @property
    def base_final_price(self):
        return self.discount_price or self.price

    def stock_total(self) -> int:
        # جمع موجودی همهٔ واریانت‌ها
        return sum(self.variations.values_list("stock", flat=True))


# -------------------- Product Image (گالری) --------------------
class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(_("تصویر"), upload_to="products/gallery/%Y/%m/")
    alt_text = models.CharField(_("متن جایگزین"), max_length=150, blank=True)
    is_main = models.BooleanField(_("تصویر اصلی؟"), default=False)

    class Meta:
        verbose_name = _("تصویر محصول")
        verbose_name_plural = _("تصاویر محصول")
        ordering = ["-is_main"]

    def __str__(self):
        return f"تصویر {self.product.name}"


# -------------------- Product Variation (رنگ×سایز با SKU/موجودی/قیمت) --------------------
class ProductVariation(models.Model):
    product = models.ForeignKey(Product, related_name="variations", on_delete=models.CASCADE)

    color = models.ForeignKey(Color, related_name="variations", on_delete=models.PROTECT, null=True, blank=True)
    size = models.ForeignKey(Size, related_name="variations", on_delete=models.PROTECT, null=True, blank=True)

    sku = models.CharField(_("SKU"), max_length=40, unique=True,
                           help_text=_("کد یکتا برای انبار/فروش"))
    barcode = models.CharField(_("بارکد"), max_length=64, blank=True)

    price_override = models.DecimalField(_("قیمت اختصاصی"), max_digits=12, decimal_places=2,
                                         null=True, blank=True,
                                         help_text=_("اگر خالی باشد از قیمت محصول استفاده می‌شود"))
    stock = models.PositiveIntegerField(_("موجودی"), default=0)
    is_active = models.BooleanField(_("فعال"), default=True)
    image = models.ImageField(_("تصویر واریانت (اختیاری)"), upload_to="products/variants/%Y/%m/",
                              null=True, blank=True)

    class Meta:
        verbose_name = _("واریانت محصول")
        verbose_name_plural = _("واریانت‌های محصول")
        ordering = ["product", "color__name", "size__sort_order", "size__name"]
        constraints = [
            # در هر محصول، ترکیب رنگ+سایز باید یکتا باشد
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
        if self.color: parts.append(self.color.name)
        if self.size: parts.append(self.size.name)
        suffix = " / ".join(parts) if parts else "بدون ویژگی"
        return f"{self.product.name} — {suffix}"

    @property
    def final_price(self):
        # اگر قیمت اختصاصی دارد، همان؛ وگرنه قیمت/تخفیف محصول
        return self.price_override or self.product.base_final_price
