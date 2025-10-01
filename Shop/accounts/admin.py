from django.contrib import admin
from .models import Province, City, User, Profile, Address
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .forms import UserRegisterForm, UserProfileForm

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = UserRegisterForm
    form = UserProfileForm
    model = User
    list_display = ("email", "username", "first_name", "last_name", "is_staff", "is_active")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("email", "username", "first_name", "last_name")
    ordering = ("-date_joined",)
    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        (_("اطلاعات شخصی"), {"fields": ("first_name", "last_name")}),
        (_("دسترسی‌ها"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("تاریخ‌های مهم"), {"fields": ("last_login", "date_joined")}),
    )
    readonly_fields = ("last_login", "date_joined")
    add_fieldsets = ((None, {"classes": ("wide",),
        "fields": ("email", "username", "first_name", "last_name", "password1", "password2", "is_active", "is_staff"),}),)
    filter_horizontal = ("groups", "user_permissions")

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "is_phone_verified", "date_of_birth")
    search_fields = ("user__username", "user__email", "phone")

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "province", "city", "address_exact", "postal_code", "is_default")
    list_filter = ("province", "city", "is_default")
    search_fields = ("full_name", "address_exact", "city__name", "province__name", "postal_code", "user__username", "user__email")

@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name", "province")
    list_filter = ("province",)
    search_fields = ("name", "province__name")
