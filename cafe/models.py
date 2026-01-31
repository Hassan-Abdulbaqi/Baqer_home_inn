from django.db import models
from django.utils import timezone


class Category(models.Model):
    """تصنيفات القائمة - Menu Categories"""
    name = models.CharField(max_length=100, verbose_name='اسم التصنيف')
    order = models.PositiveIntegerField(default=0, verbose_name='ترتيب العرض')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')

    class Meta:
        verbose_name = 'تصنيف'
        verbose_name_plural = 'التصنيفات'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    """عناصر القائمة - Menu Items"""
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name='items',
        verbose_name='التصنيف'
    )
    name = models.CharField(max_length=200, verbose_name='اسم الصنف')
    price = models.PositiveIntegerField(verbose_name='السعر (د.ع)')
    description = models.TextField(blank=True, verbose_name='الوصف')
    image = models.ImageField(
        upload_to='menu_items/', 
        blank=True, 
        null=True,
        verbose_name='الصورة'
    )
    is_available = models.BooleanField(default=True, verbose_name='متوفر')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')

    class Meta:
        verbose_name = 'صنف'
        verbose_name_plural = 'الأصناف'
        ordering = ['category__order', 'name']

    def __str__(self):
        return f"{self.name} - {self.price:,} د.ع"
    
    @property
    def formatted_price(self):
        return f"{self.price:,} د.ع"


class Order(models.Model):
    """الطلبات - Orders"""
    order_number = models.CharField(max_length=20, unique=True, verbose_name='رقم الطلب')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='تاريخ ووقت الطلب')
    total_amount = models.PositiveIntegerField(default=0, verbose_name='المجموع (د.ع)')
    amount_paid = models.PositiveIntegerField(default=0, verbose_name='المبلغ المدفوع (د.ع)')
    change_given = models.PositiveIntegerField(default=0, verbose_name='الباقي (د.ع)')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    is_printed = models.BooleanField(default=False, verbose_name='تمت الطباعة')

    class Meta:
        verbose_name = 'طلب'
        verbose_name_plural = 'الطلبات'
        ordering = ['-created_at']

    def __str__(self):
        return f"طلب #{self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            from django.db import IntegrityError
            
            today = timezone.now()
            date_prefix = today.strftime('%Y%m%d')
            
            max_attempts = 10
            for attempt in range(max_attempts):
                # Get the highest order number for today (more reliable than count)
                last_order = Order.objects.filter(
                    order_number__startswith=date_prefix
                ).order_by('-order_number').first()
                
                if last_order:
                    try:
                        last_seq = int(last_order.order_number.split('-')[-1])
                    except (ValueError, IndexError):
                        last_seq = 0
                else:
                    last_seq = 0
                
                self.order_number = f"{date_prefix}-{last_seq + 1:04d}"
                
                try:
                    super().save(*args, **kwargs)
                    return  # Success, exit the method
                except IntegrityError as e:
                    if 'order_number' in str(e) and attempt < max_attempts - 1:
                        # Unique constraint failed, retry with next number
                        self.pk = None  # Reset PK for retry
                        continue
                    raise  # Re-raise other errors or on last attempt
        else:
            super().save(*args, **kwargs)
    
    @property
    def formatted_total(self):
        return f"{self.total_amount:,} د.ع"
    
    @property
    def formatted_paid(self):
        return f"{self.amount_paid:,} د.ع"
    
    @property
    def formatted_change(self):
        return f"{self.change_given:,} د.ع"


class OrderItem(models.Model):
    """عناصر الطلب - Order Items"""
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE, 
        related_name='items',
        verbose_name='الطلب'
    )
    menu_item = models.ForeignKey(
        MenuItem, 
        on_delete=models.SET_NULL, 
        null=True,
        verbose_name='الصنف'
    )
    item_name = models.CharField(max_length=200, verbose_name='اسم الصنف')
    quantity = models.PositiveIntegerField(default=1, verbose_name='الكمية')
    unit_price = models.PositiveIntegerField(verbose_name='سعر الوحدة (د.ع)')
    subtotal = models.PositiveIntegerField(verbose_name='المجموع الفرعي (د.ع)')

    class Meta:
        verbose_name = 'عنصر طلب'
        verbose_name_plural = 'عناصر الطلبات'

    def __str__(self):
        return f"{self.item_name} x{self.quantity}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate subtotal
        self.subtotal = self.unit_price * self.quantity
        
        # Store item name for historical reference
        if self.menu_item and not self.item_name:
            self.item_name = self.menu_item.name
        
        super().save(*args, **kwargs)
    
    @property
    def formatted_subtotal(self):
        return f"{self.subtotal:,} د.ع"
