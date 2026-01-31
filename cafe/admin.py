from django.contrib import admin
from django.utils.html import format_html
from .models import Category, MenuItem, Order, OrderItem


# Customize admin site header for Arabic
admin.site.site_header = 'هوم إن كافيه - لوحة التحكم'
admin.site.site_title = 'هوم إن كافيه'
admin.site.index_title = 'إدارة المقهى'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'is_active', 'items_count', 'created_at']
    list_editable = ['order', 'is_active']
    search_fields = ['name']
    list_filter = ['is_active']
    ordering = ['order']
    
    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'عدد الأصناف'


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'display_price', 'is_available', 'image_preview']
    list_editable = ['is_available']
    list_filter = ['category', 'is_available']
    search_fields = ['name', 'description']
    ordering = ['category__order', 'name']
    
    fieldsets = (
        ('معلومات الصنف', {
            'fields': ('name', 'category', 'price', 'description')
        }),
        ('الصورة والحالة', {
            'fields': ('image', 'is_available')
        }),
    )
    
    def display_price(self, obj):
        return f"{obj.price:,} د.ع"
    display_price.short_description = 'السعر'
    display_price.admin_order_field = 'price'
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 4px;" />', obj.image.url)
        return '-'
    image_preview.short_description = 'الصورة'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['item_name', 'quantity', 'unit_price', 'subtotal']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'created_at', 'display_total', 'display_paid', 'display_change', 'is_printed']
    list_filter = ['is_printed', 'created_at']
    search_fields = ['order_number']
    readonly_fields = ['order_number', 'created_at', 'total_amount', 'amount_paid', 'change_given']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline]
    
    def display_total(self, obj):
        return f"{obj.total_amount:,} د.ع"
    display_total.short_description = 'المجموع'
    
    def display_paid(self, obj):
        return f"{obj.amount_paid:,} د.ع"
    display_paid.short_description = 'المدفوع'
    
    def display_change(self, obj):
        return f"{obj.change_given:,} د.ع"
    display_change.short_description = 'الباقي'
    
    def has_add_permission(self, request):
        return False  # Orders are created through the POS only


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'item_name', 'quantity', 'unit_price', 'subtotal']
    list_filter = ['order__created_at']
    search_fields = ['item_name', 'order__order_number']
    readonly_fields = ['order', 'menu_item', 'item_name', 'quantity', 'unit_price', 'subtotal']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
