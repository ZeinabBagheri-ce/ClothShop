from django import forms


class AddToCartForm(forms.Form):
    variation_id = forms.IntegerField(widget=forms.HiddenInput())
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "style": "max-width:120px"}
        ),
    )
