from django.core.management.base import BaseCommand
from cafe.models import Category, MenuItem


class Command(BaseCommand):
    help = 'Load sample menu data for Home Inn Cafe'

    def handle(self, *args, **options):
        # Create categories
        categories_data = [
            {'name': 'المشروبات الساخنة', 'order': 1},
            {'name': 'المشروبات الباردة', 'order': 2},
            {'name': 'العصائر الطازجة', 'order': 3},
            {'name': 'الحلويات', 'order': 4},
            {'name': 'المأكولات الخفيفة', 'order': 5},
        ]

        for cat_data in categories_data:
            Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'order': cat_data['order']}
            )
            self.stdout.write(f"Created category: {cat_data['name']}")

        # Get categories
        hot_drinks = Category.objects.get(name='المشروبات الساخنة')
        cold_drinks = Category.objects.get(name='المشروبات الباردة')
        juices = Category.objects.get(name='العصائر الطازجة')
        desserts = Category.objects.get(name='الحلويات')
        snacks = Category.objects.get(name='المأكولات الخفيفة')

        # Menu items data
        menu_items = [
            # Hot drinks
            {'category': hot_drinks, 'name': 'شاي عراقي', 'price': 1500},
            {'category': hot_drinks, 'name': 'قهوة عربية', 'price': 2000},
            {'category': hot_drinks, 'name': 'قهوة تركية', 'price': 2500},
            {'category': hot_drinks, 'name': 'نسكافيه', 'price': 3000},
            {'category': hot_drinks, 'name': 'كابتشينو', 'price': 4000},
            {'category': hot_drinks, 'name': 'لاتيه', 'price': 4500},
            {'category': hot_drinks, 'name': 'موكا', 'price': 5000},
            {'category': hot_drinks, 'name': 'هوت شوكولت', 'price': 4000},
            
            # Cold drinks
            {'category': cold_drinks, 'name': 'آيس كوفي', 'price': 5000},
            {'category': cold_drinks, 'name': 'آيس لاتيه', 'price': 5500},
            {'category': cold_drinks, 'name': 'فرابتشينو', 'price': 6000},
            {'category': cold_drinks, 'name': 'سموذي فراولة', 'price': 5500},
            {'category': cold_drinks, 'name': 'سموذي مانجو', 'price': 5500},
            {'category': cold_drinks, 'name': 'ميلك شيك', 'price': 5000},
            {'category': cold_drinks, 'name': 'موهيتو', 'price': 4500},
            
            # Juices
            {'category': juices, 'name': 'عصير برتقال طازج', 'price': 4000},
            {'category': juices, 'name': 'عصير ليمون بالنعناع', 'price': 3500},
            {'category': juices, 'name': 'عصير تفاح', 'price': 3500},
            {'category': juices, 'name': 'عصير رمان', 'price': 5000},
            {'category': juices, 'name': 'كوكتيل فواكه', 'price': 5500},
            
            # Desserts
            {'category': desserts, 'name': 'كيكة الشوكولاتة', 'price': 5000},
            {'category': desserts, 'name': 'تشيز كيك', 'price': 6000},
            {'category': desserts, 'name': 'براوني', 'price': 4000},
            {'category': desserts, 'name': 'تيراميسو', 'price': 6500},
            {'category': desserts, 'name': 'كريم كراميل', 'price': 4500},
            {'category': desserts, 'name': 'آيس كريم', 'price': 3500},
            
            # Snacks
            {'category': snacks, 'name': 'سندويش كلوب', 'price': 8000},
            {'category': snacks, 'name': 'سندويش جبنة', 'price': 5000},
            {'category': snacks, 'name': 'كرواسون', 'price': 3000},
            {'category': snacks, 'name': 'بيتزا صغيرة', 'price': 7000},
            {'category': snacks, 'name': 'سلطة سيزر', 'price': 6000},
        ]

        for item_data in menu_items:
            MenuItem.objects.get_or_create(
                name=item_data['name'],
                defaults={
                    'category': item_data['category'],
                    'price': item_data['price']
                }
            )
            self.stdout.write(f"Created menu item: {item_data['name']}")

        self.stdout.write(self.style.SUCCESS('\nSample data loaded successfully!'))
        self.stdout.write(f"Categories: {Category.objects.count()}")
        self.stdout.write(f"Menu Items: {MenuItem.objects.count()}")
