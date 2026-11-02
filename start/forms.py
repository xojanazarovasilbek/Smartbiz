from django import forms
from .models import GugurtProduct, GugurtImportBatch


class GugurtImportForm(forms.ModelForm):
    quantity_tonna = forms.DecimalField(
        label="Miqdor (tonna)",
        min_value=0.01,
        max_digits=14,
        decimal_places=2,
        required=False,
    )

    class Meta:
        model = GugurtImportBatch
        fields = [
            "product",
            "batch_number",
            "country",
            "product_cost",
            "transport_cost",
            "customs_cost",
            "other_cost",
            "import_date",
            "note",
        ]

        widgets = {
            "product": forms.Select(attrs={
                "class": "form-select"
            }),
            "batch_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "IMP-2026-001"
            }),
            "country": forms.TextInput(attrs={
                "class": "form-control"
            }),
            "product_cost": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "placeholder": "Mahsulot narxi"
            }),
            "transport_cost": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01"
            }),
            "customs_cost": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01"
            }),
            "other_cost": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01"
            }),
            "import_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),
            "note": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Qo‘shimcha izoh..."
            }),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.tenant = tenant

        if tenant:
            self.fields["product"].queryset = GugurtProduct.objects.filter(
                tenant=tenant,
                is_active=True
            )

            self.fields["country"].initial = "Xitoy"

    def clean(self):
        cleaned_data = super().clean()

        quantity_tonna = cleaned_data.get("quantity_tonna")

        if not quantity_tonna or quantity_tonna <= 0:
            self.add_error(
                "quantity_tonna",
                "Miqdorni tonnada kiriting."
            )
            return cleaned_data

        cleaned_data["quantity_kg"] = quantity_tonna * 1000

        return cleaned_data



from .models import GugurtDealer, GugurtRegion


class GugurtDealerForm(forms.ModelForm):

    class Meta:
        model = GugurtDealer

        fields = [
            "region",
            "name",
            "phone",
            "address",
            "is_active",
        ]

        widgets = {
            "region": forms.Select(attrs={
                "class": "form-select form-select-lg",
            }),

            "name": forms.TextInput(attrs={
                "class": "form-control form-control-lg",
                "placeholder": "Masalan: ABC Trade",
            }),

            "phone": forms.TextInput(attrs={
                "class": "form-control form-control-lg",
                "placeholder": "+998 90 123 45 67",
            }),

            "address": forms.TextInput(attrs={
                "class": "form-control form-control-lg",
                "placeholder": "Manzil",
            }),

            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.tenant = tenant

        if tenant:
            self.fields["region"].queryset = GugurtRegion.objects.filter(
                tenant=tenant
            )


from .models import (
    GugurtDealer,
    GugurtRegion,
    GugurtProduct,
    GugurtImportBatch,
    GugurtDistribution,
)


class GugurtDistributionForm(forms.ModelForm):

    class Meta:
        model = GugurtDistribution

        fields = [
            "batch",
            "dealer",
            "quantity_kg",
            "status",
            "dispatch_date",
            "note",
        ]

        widgets = {
            "batch": forms.Select(attrs={
                "class": "form-select form-select-lg",
            }),

            "dealer": forms.Select(attrs={
                "class": "form-select form-select-lg",
            }),

            "quantity_kg": forms.NumberInput(attrs={
                "class": "form-control form-control-lg",
                "placeholder": "Masalan: 5000",
                "step": "0.01",
                "min": "0.01",
            }),

            "status": forms.Select(attrs={
                "class": "form-select form-select-lg",
            }),

            "dispatch_date": forms.DateInput(attrs={
                "class": "form-control form-control-lg",
                "type": "date",
            }),

            "note": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Qo‘shimcha izoh...",
            }),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.tenant = tenant

        if tenant:

            self.fields["batch"].queryset = (
                GugurtImportBatch.objects
                .filter(
                    tenant=tenant,
                    product__is_active=True,
                )
                .select_related("product")
                .order_by("-import_date", "-id")
            )

            self.fields["dealer"].queryset = (
                GugurtDealer.objects
                .filter(
                    tenant=tenant,
                    is_active=True,
                )
                .select_related("region")
                .order_by("name")
            )