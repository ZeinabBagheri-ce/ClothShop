from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator


class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError(_("کاربر باید ایمیل داشته باشد"))
        if not username:
            raise ValueError(_("کاربر باید نام کاربری داشته باشد"))
        email = self.normalize_email(email)
        username = username.strip()
        user = self.model(email=email, username=username, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("سوپر یوزر باید is_staff=True داشته باشد"))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("سوپر یوزر باید is_superuser=True داشته باشد"))
        if not password:
            raise ValueError(_("برای سوپر یوزر باید گذرواژه تعیین کنید"))
        return self.create_user(email, username, password, **extra_fields)

    def get_by_natural_key(self, identifier: str):
        return self.get(Q(email__iexact=identifier) | Q(username__iexact=identifier))

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_("ایمیل"), unique=True, db_index=True)
    username = models.CharField(
        _("نام کاربری"),
        max_length=50,
        unique=True,
        db_index=True,
        validators=[RegexValidator(r"^[\w.@+-]+$", _("فقط حروف، اعداد و . @ + - _"))],
    )
    first_name = models.CharField(_("نام"), max_length=50, blank=True)
    last_name  = models.CharField(_("نام خانوادگی"), max_length=50, blank=True)

    is_active = models.BooleanField(_("فعال"), default=True)
    is_staff  = models.BooleanField(_("کارمند"), default=False)
    date_joined = models.DateTimeField(_("تاریخ عضویت"), default=timezone.now)

    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = _("کاربر")
        verbose_name_plural = _("کاربران")
        ordering = ["-date_joined"]

    def __str__(self):
        return self.username or self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(_("شماره موبایل"), max_length=20, unique=True, null=True, blank=True,
                             help_text=_("مثال: +09123456789"))
    is_phone_verified = models.BooleanField(_("تأیید تلفن"), default=False)
    avatar = models.ImageField(_("تصویر پروفایل"), upload_to="avatars/%Y/%m/", null=True, blank=True)
    date_of_birth = models.DateField(_("تاریخ تولد"), null=True, blank=True)

    def __str__(self):
        return f"پروفایل {self.user.username}"

class Province(models.Model):
    name = models.CharField(_("استان"), max_length=100, unique=True)
    class Meta:
        ordering = ["name"]
        verbose_name = _("استان")
        verbose_name_plural = _("استان‌ها")
    def __str__(self):
        return self.name

class City(models.Model):
    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name="cities")
    name = models.CharField(_("شهر"), max_length=120)
    class Meta:
        ordering = ["name"]
        unique_together = [("province", "name")]
        verbose_name = _("شهر")
        verbose_name_plural = _("شهرها")
    def __str__(self):
        return f"{self.name} ({self.province.name})"

class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="addresses")

    full_name = models.CharField(_("نام و نام خانوادگی"), max_length=100)
    phone = models.CharField(_("شماره تلفن"), max_length=20, blank=True)

    address_exact = models.CharField(_("آدرس دقیق"), max_length=255, default="نامشخص")
    description   = models.CharField(_("توضیحات"), max_length=255, blank=True)

    province = models.ForeignKey(Province, on_delete=models.PROTECT, related_name="addresses",
                                 null=True, verbose_name=_("استان"))
    city = models.ForeignKey(City, on_delete=models.PROTECT, related_name="addresses",
                             null=True, verbose_name=_("شهر"))

    postal_code = models.CharField(_("کد پستی"), max_length=20)
    # country حذف شد
    is_default = models.BooleanField(_("آدرس پیش‌فرض"), default=False)

    created_at = models.DateTimeField(_("ایجاد"), auto_now_add=True)
    updated_at = models.DateTimeField(_("به‌روزرسانی"), auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "is_default"]),
            models.Index(fields=["province", "city"]),
        ]
        verbose_name = _("آدرس")
        verbose_name_plural = _("آدرس‌ها")

    def __str__(self):
        return f"{self.full_name} - {self.city or ''}"
