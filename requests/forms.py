from django import forms
from .models import AssetRequest


class AssetRequestForm(forms.ModelForm):
    class Meta:
        model = AssetRequest
        fields = ['asset_category', 'return_date', 'remarks']
        widgets = {
            'return_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-input'}
            ),
            'remarks': forms.Textarea(
                attrs={'rows': 3, 'class': 'form-input'}
            ),
        }
        labels = {
            'asset_category': 'Asset Category',
            'return_date': 'Return Date',
            'remarks': 'Additional Remarks',
        }
