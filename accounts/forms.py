from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from .models import User

# Registration form
class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'password1', 'password2']


# Login form using email and password
class UserLoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise forms.ValidationError("Invalid email or password.")

            if not user.check_password(password):
                raise forms.ValidationError("Invalid email or password.")

            if not user.is_active:
                raise forms.ValidationError("This account is inactive.")

            cleaned_data['user'] = user  # pass the user object to view

        return cleaned_data
