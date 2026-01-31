"""
Printer service for Xprinter XP-260III thermal receipt printer.
Supports USB and Network (TCP/IP) connections.
"""

import socket
from django.conf import settings
from django.utils import timezone


# ESC/POS Commands
ESC = b'\x1b'
GS = b'\x1d'

# Initialize printer
INIT = ESC + b'@'

# Text formatting
ALIGN_LEFT = ESC + b'a\x00'
ALIGN_CENTER = ESC + b'a\x01'
ALIGN_RIGHT = ESC + b'a\x02'

# Text size
NORMAL_SIZE = GS + b'!\x00'
DOUBLE_HEIGHT = GS + b'!\x01'
DOUBLE_WIDTH = GS + b'!\x10'
DOUBLE_SIZE = GS + b'!\x11'

# Font
FONT_A = ESC + b'M\x00'
FONT_B = ESC + b'M\x01'

# Emphasis
BOLD_ON = ESC + b'E\x01'
BOLD_OFF = ESC + b'E\x00'

# Line spacing
LINE_SPACING_DEFAULT = ESC + b'2'
LINE_SPACING_SET = ESC + b'3'

# Cut paper
CUT_PARTIAL = GS + b'V\x01'
CUT_FULL = GS + b'V\x00'

# Feed
FEED_LINE = b'\n'


def get_printer_config():
    """Get printer configuration from settings"""
    return {
        'type': getattr(settings, 'PRINTER_TYPE', 'network'),
        'usb_name': getattr(settings, 'PRINTER_USB_NAME', 'XP-260III'),
        'network_ip': getattr(settings, 'PRINTER_NETWORK_IP', '192.168.1.100'),
        'network_port': getattr(settings, 'PRINTER_NETWORK_PORT', 9100),
    }


def send_to_network_printer(data: bytes, ip: str, port: int) -> tuple[bool, str]:
    """Send data to network printer via TCP/IP"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((ip, port))
        sock.sendall(data)
        sock.close()
        return True, "تمت الطباعة بنجاح"
    except socket.timeout:
        return False, "انتهت مهلة الاتصال بالطابعة"
    except ConnectionRefusedError:
        return False, "تم رفض الاتصال بالطابعة"
    except Exception as e:
        return False, f"خطأ في الطباعة: {str(e)}"


def send_to_usb_printer(data: bytes, printer_name: str) -> tuple[bool, str]:
    """Send data to USB printer via Windows print spooler"""
    try:
        import win32print
        
        # Get printer handle
        printer_handle = win32print.OpenPrinter(printer_name)
        
        try:
            # Start document
            job_id = win32print.StartDocPrinter(printer_handle, 1, ("Receipt", None, "RAW"))
            win32print.StartPagePrinter(printer_handle)
            
            # Write data
            win32print.WritePrinter(printer_handle, data)
            
            # End document
            win32print.EndPagePrinter(printer_handle)
            win32print.EndDocPrinter(printer_handle)
            
            return True, "تمت الطباعة بنجاح"
        finally:
            win32print.ClosePrinter(printer_handle)
            
    except ImportError:
        return False, "مكتبة win32print غير مثبتة"
    except Exception as e:
        return False, f"خطأ في الطباعة: {str(e)}"


def format_arabic_text(text: str) -> bytes:
    """
    Format Arabic text for thermal printer.
    Note: The XP-260III supports Arabic charset (Code Page 864).
    """
    try:
        # Try to encode as CP864 (Arabic)
        return text.encode('cp864')
    except (UnicodeEncodeError, LookupError):
        try:
            # Fallback to UTF-8
            return text.encode('utf-8')
        except:
            # Last resort: ASCII with replacement
            return text.encode('ascii', errors='replace')


def format_price(price: int) -> str:
    """Format price with IQD suffix"""
    return f"{price:,} د.ع"


def build_receipt(order, copy_type: str = "customer") -> bytes:
    """Build receipt data for printing"""
    cafe_name = getattr(settings, 'CAFE_NAME', 'هوم إن كافيه')
    cafe_name_en = getattr(settings, 'CAFE_NAME_EN', 'Home Inn Cafe')
    
    receipt = bytearray()
    
    # Initialize printer
    receipt.extend(INIT)
    
    # Header - Cafe name (centered, large)
    receipt.extend(ALIGN_CENTER)
    receipt.extend(DOUBLE_SIZE)
    receipt.extend(BOLD_ON)
    receipt.extend(format_arabic_text(cafe_name))
    receipt.extend(FEED_LINE)
    receipt.extend(NORMAL_SIZE)
    receipt.extend(format_arabic_text(cafe_name_en))
    receipt.extend(FEED_LINE)
    receipt.extend(BOLD_OFF)
    
    # Separator line
    receipt.extend(format_arabic_text("=" * 32))
    receipt.extend(FEED_LINE)
    
    # Order info
    receipt.extend(ALIGN_RIGHT)
    receipt.extend(format_arabic_text(f"رقم الطلب: {order.order_number}"))
    receipt.extend(FEED_LINE)
    
    # Date and time
    order_time = timezone.localtime(order.created_at)
    receipt.extend(format_arabic_text(f"التاريخ: {order_time.strftime('%Y/%m/%d')}"))
    receipt.extend(FEED_LINE)
    receipt.extend(format_arabic_text(f"الوقت: {order_time.strftime('%H:%M:%S')}"))
    receipt.extend(FEED_LINE)
    
    # Copy type indicator
    if copy_type == "cashier":
        receipt.extend(format_arabic_text("(نسخة الكاشير)"))
    else:
        receipt.extend(format_arabic_text("(نسخة الزبون)"))
    receipt.extend(FEED_LINE)
    
    # Separator
    receipt.extend(format_arabic_text("-" * 32))
    receipt.extend(FEED_LINE)
    
    # Items header
    receipt.extend(BOLD_ON)
    receipt.extend(format_arabic_text("الأصناف"))
    receipt.extend(FEED_LINE)
    receipt.extend(BOLD_OFF)
    receipt.extend(format_arabic_text("-" * 32))
    receipt.extend(FEED_LINE)
    
    # Order items
    for item in order.items.all():
        # Item name and quantity
        item_line = f"{item.item_name} x{item.quantity}"
        receipt.extend(format_arabic_text(item_line))
        receipt.extend(FEED_LINE)
        
        # Price (aligned right)
        receipt.extend(ALIGN_LEFT)
        price_line = f"   {format_price(item.subtotal)}"
        receipt.extend(format_arabic_text(price_line))
        receipt.extend(FEED_LINE)
        receipt.extend(ALIGN_RIGHT)
    
    # Separator
    receipt.extend(format_arabic_text("-" * 32))
    receipt.extend(FEED_LINE)
    
    # Totals
    receipt.extend(BOLD_ON)
    receipt.extend(DOUBLE_HEIGHT)
    
    # Total
    receipt.extend(format_arabic_text(f"المجموع: {format_price(order.total_amount)}"))
    receipt.extend(FEED_LINE)
    
    receipt.extend(NORMAL_SIZE)
    receipt.extend(BOLD_OFF)
    
    # Amount paid
    receipt.extend(format_arabic_text(f"المدفوع: {format_price(order.amount_paid)}"))
    receipt.extend(FEED_LINE)
    
    # Change
    if order.change_given > 0:
        receipt.extend(BOLD_ON)
        receipt.extend(format_arabic_text(f"الباقي: {format_price(order.change_given)}"))
        receipt.extend(FEED_LINE)
        receipt.extend(BOLD_OFF)
    
    # Separator
    receipt.extend(format_arabic_text("=" * 32))
    receipt.extend(FEED_LINE)
    
    # Footer
    receipt.extend(ALIGN_CENTER)
    receipt.extend(format_arabic_text("شكراً لزيارتكم"))
    receipt.extend(FEED_LINE)
    receipt.extend(format_arabic_text("Thank you for visiting"))
    receipt.extend(FEED_LINE)
    receipt.extend(FEED_LINE)
    receipt.extend(FEED_LINE)
    
    # Cut paper
    receipt.extend(CUT_PARTIAL)
    
    return bytes(receipt)


def print_receipt(order, copies: int = 2) -> tuple[bool, str]:
    """
    Print receipt for an order.
    
    Args:
        order: Order model instance
        copies: Number of copies (default 2: customer + cashier)
    
    Returns:
        tuple: (success: bool, message: str)
    """
    config = get_printer_config()
    
    # Build receipts
    copy_types = ["customer", "cashier"] if copies >= 2 else ["customer"]
    
    all_receipts = bytearray()
    for copy_type in copy_types:
        all_receipts.extend(build_receipt(order, copy_type))
    
    receipt_data = bytes(all_receipts)
    
    # Send to printer based on connection type
    if config['type'] == 'network':
        return send_to_network_printer(
            receipt_data, 
            config['network_ip'], 
            config['network_port']
        )
    else:  # USB
        return send_to_usb_printer(
            receipt_data, 
            config['usb_name']
        )
