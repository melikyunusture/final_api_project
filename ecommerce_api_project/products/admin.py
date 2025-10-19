from django.contrib import admin

# Register your models here.

from .models import Category, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    list_filter = ['created_at']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock_quantity', 'is_active', 'created_date']
    list_filter = ['category', 'is_active', 'created_date']
    search_fields = ['name', 'description']
    readonly_fields = ['created_date', 'updated_date']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'image_url')
        }),
        ('Pricing & Stock', {
            'fields': ('price', 'stock_quantity', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_date', 'updated_date')
        }),
    )