from django import forms
from .models import Asset

class AssetForm(forms.ModelForm):
    asset_category = forms.ChoiceField(
        choices=[('', 'Select Asset Category')] + Asset.CATEGORY_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'border border-gray-300 rounded-lg px-4 py-2 w-full'})
    )
    model = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Enter model'})
    )
    serial_number = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Enter unique serial number'})
    )
    barcode = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Enter unique barcode'})
    )
    specification = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Enter specifications'})
    )
    description = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Enter description'})
    )
    status = forms.ChoiceField(
        choices=[('', 'Select Status')] + Asset.STATUS_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'border border-gray-300 rounded-lg px-4 py-2 w-full'})
    )
    asset_condition = forms.ChoiceField(
        choices=[('', 'Select Condition')] + Asset.CONDITION_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'border border-gray-300 rounded-lg px-4 py-2 w-full'})
    )

    class Meta:
        model = Asset
        fields = [
            'asset_category', 'model', 'serial_number', 'barcode', 'specification',
            'description', 'status', 'asset_condition'
        ]
