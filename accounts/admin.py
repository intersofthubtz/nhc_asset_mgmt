from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django import forms
from .models import User

class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserAdminForm

    # Fields to display in list view
    list_display = ('id', 'username', 'email', 'role', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email')
    ordering = ('id',)

    # Add role to fieldsets for editing
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Read-only logic for superusers editing themselves
    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))

        # Superuser cannot change own role
        if obj and obj.is_superuser and request.user == obj:
            readonly.append('role')
        return readonly

    # Automatically set superuser role to admin
    def save_model(self, request, obj, form, change):
        if obj.is_superuser:
            obj.role = 'admin'
        super().save_model(request, obj, form, change)
