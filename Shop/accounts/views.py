from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import views as auth_views
from django.urls import reverse
from django.http import JsonResponse
from .models import City
from .forms import *

# ---------- Auth ----------
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


# ---------- Profile (User + Profile + Addresses formset) ----------
@login_required
def user_profile(request):
    show_password_changed = request.GET.get("password_changed") == "1"
    user = request.user

    if request.method == "POST":
        user_form = UserProfileForm(request.POST, instance=user)
        profile_form = ProfileExtrasForm(request.POST, request.FILES, instance=user.profile)
        formset = AddressFormSet(request.POST, instance=user)
        if user_form.is_valid() and profile_form.is_valid() and formset.is_valid():
            user_form.save()
            profile_form.save()
            formset.save()
            messages.success(request, _("پروفایل و آدرس‌ها به‌روزرسانی شدند"))
            return redirect("accounts:profile")
        else:
            # ---- فقط برای دیباگ؛ بعد از حل مشکل می‌تونی حذفش کنی
            from pprint import pprint
            print("user_form errors:", user_form.errors)
            print("profile_form errors:", profile_form.errors)
            print("formset non_form_errors:", formset.non_form_errors())
            print("formset errors:", [f.errors for f in formset.forms])
    else:
        user_form = UserProfileForm(instance=user, initial={"email": user.email})
        profile_form = ProfileExtrasForm(instance=user.profile)
        formset = AddressFormSet(instance=user)

    return render(
        request,
        "accounts/profile.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
            "formset": formset,
            "show_password_changed": show_password_changed,
        },
    )


# ---------- Password Change (redirect back to profile with modal) ----------
class CustomPasswordChangeView(auth_views.PasswordChangeView):
    template_name = "accounts/password_change.html"
    form_class = BootstrapPasswordChangeForm

    def get_success_url(self):
        return reverse("accounts:profile") + "?password_changed=1"

@login_required
def cities_by_province(request):
    prov_id = request.GET.get("province_id")
    qs = City.objects.filter(province_id=prov_id).order_by("name") if prov_id else City.objects.none()
    data = [{"id": c.id, "name": c.name} for c in qs]
    return JsonResponse({"results": data})