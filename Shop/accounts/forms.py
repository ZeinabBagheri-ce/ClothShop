from django.utils.translation import gettext_lazy as _
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from .models import Profile, Address, Province, City
from django import forms
from django.forms import inlineformset_factory
from products.models import Product, ProductVariation, Color, Size
from orders.models import Order

User = get_user_model()

class UserRegisterForm(forms.ModelForm):
    password1 = forms.CharField(label=_("گذرواژه"), widget=forms.PasswordInput(attrs={"class": "form-control"}))
    password2 = forms.CharField(label=_("تکرار گذرواژه"), widget=forms.PasswordInput(attrs={"class": "form-control"}))

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]
        widgets = {
            "username":   forms.TextInput(attrs={"class": "form-control", "autocomplete": "username"}),
            "first_name": forms.TextInput(attrs={"class": "form-control", "autocomplete": "given-name"}),
            "last_name":  forms.TextInput(attrs={"class": "form-control", "autocomplete": "family-name"}),
            "email":      forms.EmailInput(attrs={"class": "form-control", "autocomplete": "email"}),
        }

    def clean_password1(self):
        p1 = self.cleaned_data.get("password1")
        if p1:
            try:
                validate_password(p1)
            except ValidationError as e:
                raise forms.ValidationError(e.messages)
        return p1

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError(_("گذرواژه‌ها یکسان نیستند"))
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserLoginForm(forms.Form):
    username = forms.CharField(label=_("ایمیل یا نام کاربری"),
                               widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "username"}))
    password = forms.CharField(label=_("گذرواژه"),
                               widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "current-password"}))


# ---------- Profile (basic) ----------
class UserProfileForm(forms.ModelForm):
    email = forms.EmailField(label=_("ایمیل"), disabled=True, required=False,
                             widget=forms.EmailInput(attrs={"class": "form-control"}))

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]
        widgets = {
            "username":   forms.TextInput(attrs={"class": "form-control", "autocomplete": "username"}),
            "first_name": forms.TextInput(attrs={"class": "form-control", "autocomplete": "given-name"}),
            "last_name":  forms.TextInput(attrs={"class": "form-control", "autocomplete": "family-name"}),
        }
        labels = {
            "username": _("نام کاربری"),
            "first_name": _("نام"),
            "last_name": _("نام خانوادگی"),
        }


class ProfileExtrasForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["phone", "avatar", "date_of_birth"]
        widgets = {
            "phone":          forms.TextInput(attrs={"class": "form-control", "placeholder": "+98912..."}),
            "avatar":         forms.ClearableFileInput(attrs={"class": "form-control"}),
            "date_of_birth":  forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }
        labels = {
            "phone": _("شماره موبایل"),
            "avatar": _("تصویر پروفایل"),
            "date_of_birth": _("تاریخ تولد"),
        }


class AddressForm(forms.ModelForm):
    province = forms.ModelChoiceField(
        label=_("استان"),
        queryset=Province.objects.all(),
        widget=forms.Select(attrs={"class": "form-select"}),
        required=True,
    )
    city = forms.ModelChoiceField(
        label=_("شهر"),
        queryset=City.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
        required=True,
    )

    class Meta:
        model = Address
        fields = [
            "full_name", "phone",
            "province", "city",
            "address_exact", "description",
            "postal_code",
            "is_default",
        ]
        widgets = {
            "full_name":     forms.TextInput(attrs={"class": "form-control"}),
            "phone":         forms.TextInput(attrs={"class": "form-control"}),
            "address_exact": forms.TextInput(attrs={"class": "form-control", "placeholder": "مثلاً: خیابان ... پلاک ..."}),
            "description":   forms.TextInput(attrs={"class": "form-control", "placeholder": "واحد/طبقه یا توضیح اضافی"}),
            "postal_code":   forms.TextInput(attrs={"class": "form-control"}),
            "is_default":    forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "address_exact": _("آدرس دقیق"),
            "description":   _("توضیحات"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.province_id:
            self.fields["city"].queryset = City.objects.filter(province_id=self.instance.province_id)
        else:
            data = self.data or None
            if data and self.prefix:
                prov_key = f"{self.prefix}-province"
                prov_id = data.get(prov_key)
                if prov_id:
                    self.fields["city"].queryset = City.objects.filter(province_id=prov_id)

AddressFormSet = inlineformset_factory(
    parent_model=get_user_model(),
    model=Address,
    form=AddressForm,
    extra=0,
    can_delete=True,
)


class BootstrapPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.setdefault("class", "form-control")
        self.fields["old_password"].widget.attrs.setdefault("autocomplete", "current-password")
        self.fields["new_password1"].widget.attrs.setdefault("autocomplete", "new-password")
        self.fields["new_password2"].widget.attrs.setdefault("autocomplete", "new-password")

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["category", "brand", "name", "slug", "description",
                  "price", "discount_price", "is_active", "image"]

VariationFormSet = inlineformset_factory(
    parent_model=Product,
    model=ProductVariation,
    fields=["color", "size", "sku", "price_override", "stock", "is_active", "image"],
    extra=1, can_delete=True
)

class ColorForm(forms.ModelForm):
    class Meta:
        model = Color
        fields = ["name", "hex_code", "code"]

class SizeForm(forms.ModelForm):
    class Meta:
        model = Size
        fields = ["name", "sort_order", "code"]

class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["status"]
