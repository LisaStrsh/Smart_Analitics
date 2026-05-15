from django.contrib import admin
from .models import UserProfile, Dataset, ColumnMapping


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name', 'created_at')
    search_fields = ('user__username', 'company_name')


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'original_filename', 'status', 'rows_count', 'columns_count', 'uploaded_at')
    list_filter = ('status', 'uploaded_at')
    search_fields = ('name', 'original_filename')


@admin.register(ColumnMapping)
class ColumnMappingAdmin(admin.ModelAdmin):
    list_display = ('dataset', 'user_column_name', 'standard_name')
    list_filter = ('standard_name',)
