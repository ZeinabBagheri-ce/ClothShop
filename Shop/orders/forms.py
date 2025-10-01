
from django import forms
from accounts.models import Address

class CheckoutForm(forms.Form):
    address_id = forms.ModelChoiceField(
        queryset=Address.objects.none(), required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="انتخاب آدرس", empty_label="انتخاب کنید",
    )
    use_new_address = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput())
    note = forms.CharField(required=False, widget=forms.Textarea(attrs={"class":"form-control","rows":3}), label="توضیحات سفارش")
    coupon_code = forms.CharField(required=False, max_length=40,
                                  widget=forms.TextInput(attrs={"class":"form-control","placeholder":"مثلاً: OFF10"}),
                                  label="کد تخفیف")

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["address_id"].queryset = Address.objects.filter(user=user).order_by("-is_default", "-updated_at")