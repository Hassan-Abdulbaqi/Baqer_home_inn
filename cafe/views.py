import json
from datetime import datetime, timedelta
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.conf import settings

from .models import Category, MenuItem, Order, OrderItem
# Printing disabled - uncomment below to enable
# from .printer import print_receipt


def cashier_view(request):
    """نقطة البيع - POS Cashier View"""
    categories = Category.objects.filter(is_active=True).prefetch_related('items')
    context = {
        'categories': categories,
        'cafe_name': getattr(settings, 'CAFE_NAME', 'هوم إن كافيه'),
    }
    return render(request, 'cafe/cashier.html', context)


def menu_management_view(request):
    """إدارة القائمة - Menu Management View"""
    context = {
        'cafe_name': getattr(settings, 'CAFE_NAME', 'هوم إن كافيه'),
    }
    return render(request, 'cafe/menu_management.html', context)


def statistics_view(request):
    """صفحة الإحصائيات - Statistics Dashboard"""
    context = {
        'cafe_name': getattr(settings, 'CAFE_NAME', 'هوم إن كافيه'),
    }
    return render(request, 'cafe/statistics.html', context)


def orders_view(request):
    """صفحة الطلبات السابقة - Past Orders View"""
    context = {
        'cafe_name': getattr(settings, 'CAFE_NAME', 'هوم إن كافيه'),
    }
    return render(request, 'cafe/orders.html', context)


@require_http_methods(["GET"])
def api_menu(request):
    """API: Get all menu items grouped by category"""
    categories = Category.objects.filter(is_active=True).prefetch_related('items')
    
    data = []
    for category in categories:
        cat_data = {
            'id': category.id,
            'name': category.name,
            'items': []
        }
        for item in category.items.filter(is_available=True):
            cat_data['items'].append({
                'id': item.id,
                'name': item.name,
                'price': item.price,
                'description': item.description,
                'image': item.image.url if item.image else None,
            })
        data.append(cat_data)
    
    return JsonResponse({'categories': data})


@csrf_exempt
@require_http_methods(["POST"])
def api_create_order(request):
    """API: Create a new order"""
    try:
        data = json.loads(request.body)
        items = data.get('items', [])
        amount_paid = data.get('amount_paid', 0)
        
        if not items:
            return JsonResponse({'success': False, 'error': 'لا توجد أصناف في الطلب'}, status=400)
        
        # Calculate total
        total_amount = 0
        order_items_data = []
        
        for item_data in items:
            menu_item = MenuItem.objects.get(id=item_data['id'])
            quantity = item_data.get('quantity', 1)
            subtotal = menu_item.price * quantity
            total_amount += subtotal
            
            order_items_data.append({
                'menu_item': menu_item,
                'item_name': menu_item.name,
                'quantity': quantity,
                'unit_price': menu_item.price,
                'subtotal': subtotal,
            })
        
        # Calculate change
        change_given = max(0, amount_paid - total_amount)
        
        # Create order
        order = Order.objects.create(
            total_amount=total_amount,
            amount_paid=amount_paid,
            change_given=change_given,
        )
        
        # Create order items
        for item_data in order_items_data:
            OrderItem.objects.create(
                order=order,
                **item_data
            )
        
        return JsonResponse({
            'success': True,
            'order': {
                'id': order.id,
                'order_number': order.order_number,
                'total_amount': order.total_amount,
                'amount_paid': order.amount_paid,
                'change_given': order.change_given,
                'created_at': order.created_at.isoformat(),
            }
        })
        
    except MenuItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'صنف غير موجود'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_print_receipt(request, order_id):
    """API: Print receipt for an order (DISABLED)"""
    # Printing functionality has been disabled
    return JsonResponse({
        'success': False, 
        'error': 'الطباعة معطلة حالياً - Printing is disabled'
    }, status=501)


@require_http_methods(["GET"])
def api_statistics(request):
    """API: Get sales statistics"""
    try:
        # Get date range from query params
        period = request.GET.get('period', 'today')
        
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        if period == 'today':
            start_date = today_start
        elif period == 'week':
            start_date = today_start - timedelta(days=7)
        elif period == 'month':
            start_date = today_start - timedelta(days=30)
        else:
            start_date = today_start
        
        # Get orders in date range
        orders = Order.objects.filter(created_at__gte=start_date)
        
        # Calculate statistics
        total_orders = orders.count()
        total_revenue = orders.aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Daily breakdown
        daily_stats = orders.annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            orders_count=Count('id'),
            revenue=Sum('total_amount')
        ).order_by('date')
        
        # Top selling items
        top_items = OrderItem.objects.filter(
            order__created_at__gte=start_date
        ).values('item_name').annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum('subtotal')
        ).order_by('-total_quantity')[:10]
        
        return JsonResponse({
            'success': True,
            'period': period,
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'daily_stats': list(daily_stats),
            'top_items': list(top_items),
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ==================== Orders API ====================

@require_http_methods(["GET"])
def api_orders(request):
    """API: Get all orders with pagination and filtering"""
    try:
        # Get query parameters
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        search = request.GET.get('search', '').strip()
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        
        # Base queryset
        orders = Order.objects.prefetch_related('items').order_by('-created_at')
        
        # Apply filters
        if search:
            orders = orders.filter(order_number__icontains=search)
        
        if date_from:
            try:
                from_date = datetime.strptime(date_from, '%Y-%m-%d')
                from_date = timezone.make_aware(from_date)
                orders = orders.filter(created_at__gte=from_date)
            except ValueError:
                pass
        
        if date_to:
            try:
                to_date = datetime.strptime(date_to, '%Y-%m-%d')
                to_date = timezone.make_aware(to_date.replace(hour=23, minute=59, second=59))
                orders = orders.filter(created_at__lte=to_date)
            except ValueError:
                pass
        
        # Get total count before pagination
        total_count = orders.count()
        total_pages = (total_count + per_page - 1) // per_page
        
        # Apply pagination
        start = (page - 1) * per_page
        end = start + per_page
        orders = orders[start:end]
        
        # Serialize orders
        orders_data = []
        for order in orders:
            order_items = [{
                'item_name': item.item_name,
                'quantity': item.quantity,
                'unit_price': item.unit_price,
                'subtotal': item.subtotal,
            } for item in order.items.all()]
            
            orders_data.append({
                'id': order.id,
                'order_number': order.order_number,
                'created_at': order.created_at.isoformat(),
                'total_amount': order.total_amount,
                'amount_paid': order.amount_paid,
                'change_given': order.change_given,
                'notes': order.notes,
                'is_printed': order.is_printed,
                'items': order_items,
            })
        
        return JsonResponse({
            'success': True,
            'orders': orders_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': total_pages,
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def api_order_detail(request, order_id):
    """API: Get single order details"""
    try:
        order = Order.objects.prefetch_related('items').get(id=order_id)
        
        order_items = [{
            'item_name': item.item_name,
            'quantity': item.quantity,
            'unit_price': item.unit_price,
            'subtotal': item.subtotal,
        } for item in order.items.all()]
        
        return JsonResponse({
            'success': True,
            'order': {
                'id': order.id,
                'order_number': order.order_number,
                'created_at': order.created_at.isoformat(),
                'total_amount': order.total_amount,
                'amount_paid': order.amount_paid,
                'change_given': order.change_given,
                'notes': order.notes,
                'is_printed': order.is_printed,
                'items': order_items,
            }
        })
        
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'الطلب غير موجود'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ==================== Category Management API ====================

@csrf_exempt
@require_http_methods(["GET", "POST"])
def api_categories(request):
    """API: List all categories or create a new one"""
    try:
        if request.method == 'GET':
            categories = Category.objects.annotate(
                items_count=Count('items')
            ).order_by('order', 'name')
            
            data = [{
                'id': cat.id,
                'name': cat.name,
                'order': cat.order,
                'is_active': cat.is_active,
                'items_count': cat.items_count,
            } for cat in categories]
            
            return JsonResponse({'success': True, 'categories': data})
        
        elif request.method == 'POST':
            data = json.loads(request.body)
            
            category = Category.objects.create(
                name=data.get('name', ''),
                order=data.get('order', 0),
                is_active=data.get('is_active', True)
            )
            
            return JsonResponse({
                'success': True,
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'order': category.order,
                    'is_active': category.is_active,
                }
            })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PUT", "DELETE"])
def api_category_detail(request, category_id):
    """API: Update or delete a category"""
    try:
        category = Category.objects.get(id=category_id)
        
        if request.method == 'PUT':
            data = json.loads(request.body)
            category.name = data.get('name', category.name)
            category.order = data.get('order', category.order)
            category.is_active = data.get('is_active', category.is_active)
            category.save()
            
            return JsonResponse({
                'success': True,
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'order': category.order,
                    'is_active': category.is_active,
                }
            })
        
        elif request.method == 'DELETE':
            category.delete()
            return JsonResponse({'success': True})
            
    except Category.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'التصنيف غير موجود'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ==================== Menu Items Management API ====================

@csrf_exempt
@require_http_methods(["GET", "POST"])
def api_items(request):
    """API: List all items or create a new one"""
    try:
        if request.method == 'GET':
            category_id = request.GET.get('category')
            
            items = MenuItem.objects.select_related('category')
            if category_id:
                items = items.filter(category_id=category_id)
            
            items = items.order_by('category__order', 'name')
            
            data = [{
                'id': item.id,
                'name': item.name,
                'price': item.price,
                'description': item.description,
                'image': item.image.url if item.image else None,
                'is_available': item.is_available,
                'category_id': item.category_id,
                'category_name': item.category.name,
            } for item in items]
            
            return JsonResponse({'success': True, 'items': data})
        
        elif request.method == 'POST':
            # Handle form data (for file uploads)
            category_id = request.POST.get('category_id')
            name = request.POST.get('name', '')
            price = request.POST.get('price', 0)
            description = request.POST.get('description', '')
            is_available = request.POST.get('is_available', 'true').lower() == 'true'
            image = request.FILES.get('image')
            
            category = Category.objects.get(id=category_id)
            
            item = MenuItem.objects.create(
                category=category,
                name=name,
                price=int(price),
                description=description,
                is_available=is_available,
                image=image
            )
            
            return JsonResponse({
                'success': True,
                'item': {
                    'id': item.id,
                    'name': item.name,
                    'price': item.price,
                    'description': item.description,
                    'image': item.image.url if item.image else None,
                    'is_available': item.is_available,
                    'category_id': item.category_id,
                }
            })
    except Category.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'التصنيف غير موجود'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PUT", "DELETE"])
def api_item_detail(request, item_id):
    """API: Update or delete a menu item"""
    try:
        item = MenuItem.objects.get(id=item_id)
        
        if request.method == 'PUT':
            # Handle form data (for file uploads)
            category_id = request.POST.get('category_id')
            if category_id:
                item.category = Category.objects.get(id=category_id)
            
            item.name = request.POST.get('name', item.name)
            item.price = int(request.POST.get('price', item.price))
            item.description = request.POST.get('description', item.description)
            item.is_available = request.POST.get('is_available', 'true').lower() == 'true'
            
            if 'image' in request.FILES:
                item.image = request.FILES['image']
            
            item.save()
            
            return JsonResponse({
                'success': True,
                'item': {
                    'id': item.id,
                    'name': item.name,
                    'price': item.price,
                    'description': item.description,
                    'image': item.image.url if item.image else None,
                    'is_available': item.is_available,
                    'category_id': item.category_id,
                }
            })
        
        elif request.method == 'DELETE':
            item.delete()
            return JsonResponse({'success': True})
            
    except MenuItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'الصنف غير موجود'}, status=404)
    except Category.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'التصنيف غير موجود'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
