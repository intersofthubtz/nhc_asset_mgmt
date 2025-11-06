from django import forms
from .models import Asset, AssetCategory

class AssetCategoryForm(forms.ModelForm):
    class Meta:
        model = AssetCategory
        fields = ['name', 'description']

class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = [
            'asset_code', 'asset_name', 'model', 'serial_number', 'barcode',
            'specification', 'category', 'description', 'status', 'asset_condition',
            'purchase_date', 'assigned_to'
        ]

