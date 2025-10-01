from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import views as auth_views
from django.urls import reverse
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Prefetch
from django.views.decorators.http import require_POST
from django.forms import modelform_factory

from .forms import *  # UserRegisterForm, UserLoginForm, UserProfileForm, ProfileExtrasForm, AddressFormSet, BootstrapPasswordChangeForm
from .models import City

User = get_user_model()

# orders app (optional)
try:
    from orders.models import Order, OrderItem, Coupon
except Exception:
    Order = None
    OrderItem = None
    Coupon = None

# products app (optional)
try:
    from products.models import (
        Product, ProductVariation, Color, Size, Category, Brand
    )
except Exception:
    Product = ProductVariation = Color = Size = Category = Brand = None

# counts for sidebar (optional)
try:
    from accounts.models import Profile, Address, Province
except Exception:
    Profile = Address = Province = None


# ----------------- auth -----------------

def user_register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("ثبت‌ نام با موفقیت انجام شد. اکنون وارد شوید."))
            return redirect("home:home")
    else:
        form = UserRegisterForm()
    return render(request, "accounts/register.html", {"form": form})


def user_login(request):
    submitted = False
    if request.method == "POST":
        form = UserLoginForm(request.POST)
        submitted = True
        if form.is_valid():
            identifier = form.cleaned_data["username"]
            password   = form.cleaned_data["password"]
            user = authenticate(request, username=identifier, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, _("خوش آمدید"))
                return redirect(request.GET.get("next") or "/")
            form.add_error(None, _("ایمیل/نام کاربری یا گذرواژه نادرست است"))
    else:
        form = UserLoginForm()
    return render(request, "accounts/login.html", {"form": form, "submitted": submitted})


@login_required
def user_logout(request):
    logout(request)
    messages.info(request, _("خروج انجام شد"))
    return redirect("/")


# ----------------- profile helpers -----------------

def _build_profile_context(request):
    user = request.user
    show_password_changed = (request.GET.get("password_changed") == "1")

    # ----- user/profile/address forms -----
    if request.method == "POST" and request.POST.get("context", "profile") == "profile":
        user_form    = UserProfileForm(request.POST, instance=user)
        profile_form = ProfileExtrasForm(request.POST, request.FILES, instance=user.profile)
        formset      = AddressFormSet(request.POST, instance=user)
        if user_form.is_valid() and profile_form.is_valid() and formset.is_valid():
            user_form.save(); profile_form.save(); formset.save()
            messages.success(request, _("پروفایل و آدرس‌ها به‌روزرسانی شدند"))
            return {"redirect": True, "redirect_to": reverse("accounts:profile")}
    else:
        user_form    = UserProfileForm(instance=user, initial={"email": user.email})
        profile_form = ProfileExtrasForm(instance=user.profile)
        formset      = AddressFormSet(instance=user)

    # ----- user orders -----
    orders_qs = []; order_counts = {}; recent_orders = []; status_steps = {}
    if Order is not None:
        # برای نمایش stepper
        STATUS_ORDER = ["PENDING", "PAID", "PROCESSING", "SHIPPED", "DELIVERED"]
        step_index = {s: i for i, s in enumerate(STATUS_ORDER, start=1)}
        status_steps = step_index

        orders_qs = (
            Order.objects.filter(user=user)
            .prefetch_related(
                Prefetch("items", queryset=OrderItem.objects.select_related("variation", "variation__product"))
            )
            .order_by("-created_at")
        )
        order_counts = {
            "all": orders_qs.count(),
            "pending": orders_qs.filter(status__iexact="pending").count(),
            "paid": orders_qs.filter(status__iexact="paid").count(),
            "processing": orders_qs.filter(status__iexact="processing").count(),
            "shipped": orders_qs.filter(status__iexact="shipped").count(),
            "delivered": orders_qs.filter(status__iexact="delivered").count(),
            "canceled": orders_qs.filter(status__iexact="canceled").count(),
        }
        recent_orders = list(orders_qs[:5])
        for o in list(orders_qs) + recent_orders:
            o.step = step_index.get(str(getattr(o, "status", "")).upper(), 1)

    # ----- staff panel -----
    staff_ctx = {}
    if user.is_staff and Product is not None:
        # forms
        ProductForm   = modelform_factory(Product,   fields=["category", "brand", "name", "slug", "price", "discount_price", "is_active", "image", "description"])
        VariationForm = modelform_factory(ProductVariation, fields=["product", "color", "size", "sku", "barcode", "price_override", "stock", "is_active", "image"])
        ColorForm     = modelform_factory(Color,     fields=["name", "hex_code", "code"])
        SizeForm      = modelform_factory(Size,      fields=["name", "sort_order", "code"])
        BrandForm     = modelform_factory(Brand,     fields=[f.name for f in Brand._meta.fields if f.name in {"name","slug","is_active"} or f.name in {"name","slug"}])  # تحمل مدل بدون is_active
        CategoryForm  = modelform_factory(Category,  fields=[f.name for f in Category._meta.fields if f.name in {"name","slug","parent","is_active"} or f.name in {"name","slug","parent"}])

        # instances for rendering
        product_qf   = ProductForm()
        color_qf     = ColorForm()
        size_qf      = SizeForm()
        brand_qf     = BrandForm()
        category_qf  = CategoryForm()

        # actions
        if request.method == "POST" and request.POST.get("context") == "staff":
            action = request.POST.get("action")
            try:
                if action == "add_color":
                    f = ColorForm(request.POST)
                    if f.is_valid():
                        f.save()
                        messages.success(request, _("رنگ جدید ایجاد شد."))
                        return {"redirect": True, "redirect_to": reverse("accounts:profile")}
                    messages.error(request, _("خطا در فرم رنگ."))

                elif action == "add_size":
                    f = SizeForm(request.POST)
                    if f.is_valid():
                        f.save()
                        messages.success(request, _("سایز جدید ایجاد شد."))
                        return {"redirect": True, "redirect_to": reverse("accounts:profile")}
                    messages.error(request, _("خطا در فرم سایز."))

                elif action == "add_brand":
                    f = BrandForm(request.POST)
                    if f.is_valid():
                        f.save()
                        messages.success(request, _("برند جدید ایجاد شد."))
                        return {"redirect": True, "redirect_to": reverse("accounts:profile")}
                    messages.error(request, _("خطا در فرم برند."))

                elif action == "add_category":
                    f = CategoryForm(request.POST)
                    if f.is_valid():
                        f.save()
                        messages.success(request, _("دسته‌بندی جدید ایجاد شد."))
                        return {"redirect": True, "redirect_to": reverse("accounts:profile")}
                    messages.error(request, _("خطا در فرم دسته‌بندی."))

                elif action == "add_product":
                    f = ProductForm(request.POST, request.FILES)
                    if f.is_valid():
                        p = f.save()
                        messages.success(request, _("محصول «%(n)s» ایجاد شد.") % {"n": p.name})
                        return {"redirect": True, "redirect_to": reverse("accounts:profile")}
                    messages.error(request, _("خطا در فرم محصول."))

                elif action == "delete_product":
                    pid = request.POST.get("product_id")
                    get_object_or_404(Product, id=pid).delete()
                    messages.info(request, _("محصول حذف شد."))
                    return {"redirect": True, "redirect_to": reverse("accounts:profile")}

                elif action == "delete_variation":
                    vid = request.POST.get("variation_id")
                    get_object_or_404(ProductVariation, id=vid).delete()
                    messages.info(request, _("واریانت حذف شد."))
                    return {"redirect": True, "redirect_to": reverse("accounts:profile")}

            except Exception as e:
                messages.error(request, _("خطای غیرمنتظره: ") + str(e))
                return {"redirect": True, "redirect_to": reverse("accounts:profile")}

        # lists
        staff_products   = Product.objects.select_related("brand", "category").order_by("-id")[:50]
        staff_variations = ProductVariation.objects.select_related("product", "color", "size").order_by("-id")[:50]
        staff_colors     = Color.objects.order_by("name")
        staff_sizes      = Size.objects.order_by("sort_order", "name")
        staff_brands     = Brand.objects.order_by("name")
        staff_cats       = Category.objects.select_related("parent").order_by("name")

        # admin orders
        admin_orders = []
        if Order is not None:
            admin_orders = (
                Order.objects.select_related("user")
                .prefetch_related(Prefetch("items", queryset=OrderItem.objects.select_related("variation", "variation__product")))
                .order_by("-created_at")[:50]
            )

        # ----- GET choices of status from the field itself
        def _order_status_choices():
            if Order is None:
                return []
            try:
                field = Order._meta.get_field("status")
                # returns list of tuples: [(value, label), ...]
                return list(field.choices)
            except Exception:
                return []

        # sidebar counters
        account_counts = {
            "profiles":  Profile.objects.count()  if Profile  else 0,
            "addresses": Address.objects.count()  if Address else 0,
            "provinces": Province.objects.count() if Province else 0,
            "cities":    City.objects.count()     if City     else 0,
            "users":     User.objects.count(),
        }
        product_counts = {
            "brands":     Brand.objects.count()            if Brand            else 0,
            "categories": Category.objects.count()         if Category         else 0,
            "colors":     Color.objects.count()            if Color            else 0,
            "sizes":      Size.objects.count()             if Size             else 0,
            "products":   Product.objects.count()          if Product          else 0,
            "variations": ProductVariation.objects.count() if ProductVariation else 0,
        }
        order_counts_admin = {
            "orders":  Order.objects.count()  if Order  else 0,
            "coupons": Coupon.objects.count() if Coupon else 0,
        }

        latest_users     = User.objects.order_by("-date_joined")[:10]
        latest_addresses = Address.objects.select_related("user", "city", "province").order_by("-id")[:10] if Address else []

        staff_ctx = {
            "ProductForm": ProductForm, "VariationForm": VariationForm,
            "ColorForm": ColorForm, "SizeForm": SizeForm,
            "BrandForm": BrandForm, "CategoryForm": CategoryForm,

            "product_qf": product_qf,
            "color_qf": color_qf, "size_qf": size_qf,
            "brand_qf": brand_qf, "category_qf": category_qf,

            "staff_products": staff_products, "staff_variations": staff_variations,
            "staff_colors": staff_colors, "staff_sizes": staff_sizes,
            "staff_brands": staff_brands, "staff_categories": staff_cats,

            "admin_orders": admin_orders, "order_status_choices": _order_status_choices(),
            "sidebar_counts": {"accounts": account_counts, "products": product_counts, "orders": order_counts_admin},
            "latest_users": latest_users, "latest_addresses": latest_addresses,
        }

    ctx = {
        "user_form": user_form, "profile_form": profile_form, "formset": formset,
        "show_password_changed": show_password_changed,
        "orders": orders_qs, "order_counts": order_counts,
        "recent_orders": recent_orders, "status_steps": status_steps,
        "is_staff": user.is_staff, **staff_ctx,
    }
    return {"ctx": ctx}


# ----------------- profile views -----------------

@login_required
def user_profile(request):
    built = _build_profile_context(request)
    if built.get("redirect"): return redirect(built["redirect_to"])
    template = "accounts/profile_staff.html" if request.user.is_staff else "accounts/profile_user.html"
    return render(request, template, built["ctx"])


@login_required
def user_profile_user(request):
    built = _build_profile_context(request)
    if built.get("redirect"): return redirect(built["redirect_to"])
    return render(request, "accounts/profile_user.html", built["ctx"])


@login_required
def user_profile_staff(request):
    if not request.user.is_staff:
        return redirect("accounts:profile")
    built = _build_profile_context(request)
    if built.get("redirect"): return redirect(built["redirect_to"])
    return render(request, "accounts/profile_staff.html", built["ctx"])


# ----------------- password change -----------------

class CustomPasswordChangeView(auth_views.PasswordChangeView):
    template_name = "accounts/password_change.html"
    form_class = BootstrapPasswordChangeForm
    def get_success_url(self):
        return reverse("accounts:profile") + "?password_changed=1"


# ----------------- ajax cities -----------------

@login_required
def cities_by_province(request):
    prov_id = request.GET.get("province_id")
    qs = City.objects.filter(province_id=prov_id).order_by("name") if prov_id else City.objects.none()
    data = [{"id": c.id, "name": c.name} for c in qs]
    return JsonResponse({"results": data})


# ----------------- staff action: set order status -----------------

@login_required
@require_POST
def staff_set_order_status(request, order_id: int):
    if not request.user.is_staff or Order is None:
        return HttpResponseForbidden()

    order = get_object_or_404(Order, id=order_id)

    # مقدار خام ارسالی (ممکن است value یا حتی label باشد)
    raw = (request.POST.get("status") or "").strip()
    if not raw:
        messages.error(request, _("وضعیت نامعتبر است."))
        return redirect("accounts:profile")

    # استخراج choices واقعی از فیلد
    try:
        field = Order._meta.get_field("status")
        choices = list(field.choices)  # [(value, label), ...]
    except Exception:
        choices = []

    # نگاشت مقاوم: 1) با value دقیق 2) با label به صورت casefold
    value_by_value  = {str(v): v for v, _ in choices}
    value_by_label  = {str(lbl).casefold(): v for v, lbl in choices}

    new_value = None
    if raw in value_by_value:
        new_value = value_by_value[raw]
    else:
        new_value = value_by_label.get(raw.casefold())

    if new_value is None:
        # آخرین تلاش: شاید مدل Enum باشد و کاربر value بزرگ‌نوشته بفرستد
        try:
            enum_values = {getattr(c, "value", None): getattr(c, "value", None) for c in getattr(Order, "Status")}
            if raw in enum_values:
                new_value = enum_values[raw]
        except Exception:
            pass

    if new_value is None:
        messages.error(request, _("وضعیت نامعتبر است."))
        return redirect("accounts:profile")

    order.status = new_value
    order.save(update_fields=["status"])
    messages.success(request, _("وضعیت سفارش به «%(st)s» تغییر کرد.") % {"st": dict(choices).get(new_value, new_value)})
    return redirect("accounts:profile")
