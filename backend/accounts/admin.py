from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Society, User


@admin.register(Society)
class SocietyAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_information')
    search_fields = ('name', 'address')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_fieldsets = ((None, {
        'classes': ('wide',),
        'fields': ('username', 'email', 'password1', 'password2', 'role', 'society'),
    }),)
    list_display = ('email', 'username', 'role', 'society', 'is_staff')
    list_filter = ('role', 'society', 'is_staff')
    fieldsets = BaseUserAdmin.fieldsets + (('Society access', {'fields': ('role', 'society')}),)
