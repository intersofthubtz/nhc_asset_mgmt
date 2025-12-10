from django import forms
from .models import AssetRequest

class AssetRequestForm(forms.ModelForm):
    class Meta:
        model = AssetRequest
        fields = ['asset_category', 'request_date', 'return_date', 'remarks']
        widgets = {
            'request_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'return_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'remarks': forms.Textarea(attrs={'rows': 3, 'class': 'form-input'}),
        }
        labels = {
            'asset_category': 'Asset Category',
            'request_date': 'Request Date',
            'return_date': 'Return Date',
            'remarks': 'Additional Remarks',
        }