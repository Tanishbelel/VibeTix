from django.shortcuts import render, redirect,get_object_or_404
import time
from .models import *
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from datetime import timedelta, date
from django.db.models import Q
from django.db.models import Count
from django.http import JsonResponse
from decimal import Decimal
from .models import CartItem
import razorpay
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import uuid
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
import re
from django.views.decorators.http import require_POST


def home(request):
    products = [
        {"name": "Physics Labbook", "price": Decimal('50.00')},
        {"name": "Chemistry Labbook", "price": Decimal('50.00')},
        {"name": "Maths Labbook", "price": Decimal('50.00')},
      
    ]
    
    return render(request, 'index.html', {'products': products})

def login_page(request):
    if request.method== "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not User.objects.filter(username = username).exists():
             messages.info(request, 'Invalid Data')
             return redirect('/login/')
        user = authenticate(username = username, password = password)

        if user is None:
             messages.info(request, 'Invalid Data')
             return redirect('/login/')
        else :
            login(request, user)
            return redirect('/main/')

    return render(request, 'login.html')
    
def register_page(request):

    if request.method== "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = User.objects.filter(username = username)
        if user.exists():
            messages.info(request, 'Username already Taken')
            return redirect('/register/')

        user=User.objects.create(
            first_name = first_name,
            last_name = last_name,
            username = username,
        )
        user.set_password(password)
        user.save()


        messages.info(request, 'Account Created Successfully')

        return redirect("/login/")

    return render(request, 'register.html')

def logout_page(request):
    logout(request)
    return redirect('/login/')

@login_required(login_url = '/login/')
def main(request):
        
    return render(request , "main.html")
@login_required(login_url = '/login/')
def product_list(request):
    return render(request, 'prods.html')
@login_required
def store(request):
    products = [
        {"name": "Physics Labbook", "price": Decimal('50.00')},
        {"name": "Chemistry Labbook", "price": Decimal('50.00')},
        {"name": "Maths Labbook", "price": Decimal('50.00')},
    ]
    return render(request, 'store.html', {'products': products})

@login_required
def add_to_cart(request):
    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        price = request.POST.get('price')
        
        # Check if item already exists in cart
        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            product_name=product_name,
            defaults={'price': price}
        )
        
        if not created:
            cart_item.quantity += 1
            cart_item.save()
            
        return JsonResponse({'status': 'success', 'cart_count': get_cart_count(request.user)})
    return JsonResponse({'status': 'error'})

@login_required
def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    subtotal = sum(item.get_total() for item in cart_items)
    tax = subtotal * Decimal('0.08')  # 8% tax
    total = subtotal + tax
    
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'tax': tax,
        'total': total,
    }
    return render(request, 'cart.html', context)

@login_required
def update_quantity(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        action = request.POST.get('action')
        
        try:
            cart_item = CartItem.objects.get(id=item_id, user=request.user)
            if action == 'increase':
                cart_item.quantity += 1
            elif action == 'decrease':
                if cart_item.quantity > 1:
                    cart_item.quantity -= 1
            cart_item.save()
            
            return JsonResponse({
                'status': 'success',
                'quantity': cart_item.quantity,
                'total': float(cart_item.get_total()),
                'cart_total': float(get_cart_total(request.user))
            })
        except CartItem.DoesNotExist:
            return JsonResponse({'status': 'error'})
    return JsonResponse({'status': 'error'})

@login_required
def remove_from_cart(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        try:
            cart_item = CartItem.objects.get(id=item_id, user=request.user)
            cart_item.delete()
            return JsonResponse({'status': 'success'})
        except CartItem.DoesNotExist:
            return JsonResponse({'status': 'error'})
    return JsonResponse({'status': 'error'})

def get_cart_count(user):
    return CartItem.objects.filter(user=user).count()

def get_cart_total(user):
    cart_items = CartItem.objects.filter(user=user)
    return sum(item.get_total() for item in cart_items)
@login_required
def main(request):
    products = [
        {"name": "Physics Labbook", "price": Decimal('50.00')},
        {"name": "Chemistry Labbook", "price": Decimal('50.00')},
        {"name": "Maths Labbook", "price": Decimal('50.00')},
        {"name": "Biology Labbook", "price": Decimal('45.00')},
        {"name": "Computer Science Notes", "price": Decimal('60.00')},
        {"name": "English Grammar Book", "price": Decimal('40.00')},
        {"name": "History Notes", "price": Decimal('35.00')},
        {"name": "Geography Atlas", "price": Decimal('75.00')},
        {"name": "Economics Study Guide", "price": Decimal('55.00')}
    ]
    return render(request, 'main.html', {'products': products})



def is_admin(user):
    return user.is_staff

@never_cache
def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid admin credentials')
            
    return render(request, 'admin_login.html')

@user_passes_test(is_admin, login_url='admin_login')
def admin_dashboard(request):
    # Get total users
    total_users = User.objects.count()
    
    # Get active users (logged in within last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    active_users = User.objects.filter(last_login__gte=thirty_days_ago).count()
    
    # Example recent activities (replace with your actual activity model)
    recent_activities = [
        {
            'user': 'john_doe',
            'action': 'Created new account',
            'date': timezone.now(),
            'status': 'Success',
            'status_color': 'success'
        },
        {
            'user': 'jane_smith',
            'action': 'Updated profile',
            'date': timezone.now() - timedelta(hours=2),
            'status': 'Pending',
            'status_color': 'warning'
        }
    ]
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'recent_activities': recent_activities
    }
    
    return render(request, 'admin_dashboard.html', context)

def admin_logout(request):
    logout(request)
    return redirect('admin_login')

def create_admin_account(request):
    if request.method == 'POST':
        # Fetching form data
        fullname = request.POST.get('fullname', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        admin_code = request.POST.get('admin_code', '').strip()

        # Basic validation
        if not all([fullname, username, password, confirm_password]):
            messages.error(request, 'All fields are required.')
            return render(request, 'admin_register.html')

        # Username validation
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
            messages.error(request, 'Username must be 3-20 characters long and contain only letters, numbers, and underscores.')
            return render(request, 'admin_register.html')

        # Password validation
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return render(request, 'admin_register.html')

        if not any(c.isupper() for c in password) or not any(c.islower() for c in password) or not any(c.isdigit() for c in password):
            messages.error(request, 'Password must contain at least one uppercase letter, one lowercase letter, and one number.')
            return render(request, 'admin_register.html')

        # Password confirmation validation
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'admin_register.html')

        # Admin code validation
        if not admin_code:
            messages.error(request, 'Admin registration code is required.')
            return render(request, 'admin_register.html')

        # Verify admin code - replace 'YOUR_ADMIN_CODE' with actual code verification logic
        if not verify_admin_code(admin_code):
            messages.error(request, 'Invalid admin registration code.')
            return render(request, 'admin_register.html')

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return render(request, 'admin_register.html')

        try:
            # Creating the user with admin privileges
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=fullname,
                is_staff=True,
                is_superuser=True  # Grant full admin privileges
            )

            # Create additional admin profile if needed
            # AdminProfile.objects.create(user=user, ...)

            messages.success(request, 'Admin account created successfully.')
            return redirect('admin_login')

        except ValidationError as e:
            messages.error(request, f"Error: {', '.join(e.messages)}")
        except Exception as e:
            messages.error(request, 'An error occurred while creating the account. Please try again.')
            
    return render(request, 'admin_register.html')

def verify_admin_code(code):
    """
    Verify the admin registration code.
    Replace this with your actual verification logic.
    """

@login_required
@require_POST
def cancel_order(request):
    try:
        student = Student.objects.get(user=request.user)
        order = Order.objects.get(
            student=student,
            status='Processing'
        )
        
        order.status = 'Cancelled'
        order.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Order cancelled successfully'
        })
        
    except (Order.DoesNotExist, Student.DoesNotExist):
        return JsonResponse({
            'status': 'error',
            'message': 'Order not found or cannot be cancelled'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred while cancelling the order'
        }, status=500)
    
def is_admin(user):
    return user.is_staff and user.is_authenticated

def admin_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_orders')
    return render(request, 'admin_login.html')

def admin_logout(request):
    logout(request)
    return redirect('admin_login')

@user_passes_test(is_admin, login_url='admin_login')
def admin_orders(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'admin_panel.html', {'orders': orders})

@user_passes_test(is_admin, login_url='admin_login')
def get_order_details(request):
    order_id = request.GET.get('order_id')
    try:
        order = Order.objects.get(order_id=order_id)
        order_items = order.items.all()
        return render(request, 'order_details.html', {
            'order': order,
            'items': order_items
        })
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)

@user_passes_test(is_admin, login_url='admin_login')
def update_order_status(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        try:
            order = Order.objects.get(order_id=order_id)
            # Cycle through statuses
            status_cycle = {
                'Processing': 'Completed',
                'Completed': 'Cancelled',
                'Cancelled': 'Processing'
            }
            order.status = status_cycle[order.status]
            order.save()
            return JsonResponse({'status': 'success'})
        except Order.DoesNotExist:
            return JsonResponse({'error': 'Order not found'}, status=404)
    return JsonResponse({'error': 'Invalid request'}, status=400)

def create_order(request):
    if request.method == 'POST':
        try:
            # Get cart items for current user
            cart_items = CartItem.objects.filter(user=request.user)
            
            # Calculate totals
            subtotal = sum(item.get_total() for item in cart_items)
            platform_fee = subtotal * 0.02
            total = subtotal + platform_fee
            
            # Create order
            order = Order.objects.create(
                user=request.user,
                subtotal=subtotal,
                platform_fee=platform_fee,
                total_amount=total,
                status='Processing'
            )
            
            # Create order items
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product_name=cart_item.product_name,
                    quantity=cart_item.quantity,
                    price=cart_item.price,
                    total_price=cart_item.get_total()
                )
            
            # Clear cart
            cart_items.delete()
            
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders.html', {'orders': orders})
@login_required 
def create_order(request):
    if request.method == 'POST':
        try:
            cart_items = CartItem.objects.filter(user=request.user)
            
            # Check if cart is empty
            if not cart_items.exists():
                return JsonResponse({'status': 'error', 'message': 'Cart is empty'})
            
            # Calculate totals
            subtotal = sum(item.get_total() for item in cart_items)
            platform_fee = subtotal * Decimal('0.02')  
            total_amount = subtotal + platform_fee
            
            # Create order with a unique order number
            order = Order.objects.create(
                user=request.user,
                payment_method='Razorpay',
                subtotal=subtotal,
                platform_fee=platform_fee,
                total_amount=total_amount,
                status='PENDING',
                order_number=f"ORD-{int(time.time())}"  # Add a unique order number
            )
            
            # Create order items
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product_name=cart_item.product_name,
                    price=cart_item.price,
                    quantity=cart_item.quantity
                )
            
            # Clear cart
            cart_items.delete()
            
            # Return success with redirect URL
            return JsonResponse({
                'status': 'success',
                'redirect_url': reverse('orders')  # Add the URL name for your orders page
            })
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
@login_required
def orders(request):
    try:
        # Print debugging information
        print(f"Current user: {request.user.username}")
        
        # Get all orders for the current user
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        print(f"Number of orders found: {orders.count()}")
        
        # Print details of each order
        for order in orders:
            print(f"""
                Order details:
                - Order number: {order.order_number}
                - Status: {order.status}
                - Total: {order.total_amount}
                - Items: {order.items.all().count()}
            """)

        context = {
            'orders': orders,
            'debug_info': {
                'user': request.user.username,
                'order_count': orders.count(),
                'orders_list': [
                    {
                        'number': order.order_number,
                        'status': order.status,
                        'total': float(order.total_amount),
                        'items_count': order.items.all().count()
                    } for order in orders
                ]
            }
        }
        
        return render(request, 'orders.html', context)
        
    except Exception as e:
        print(f"Error in orders view: {str(e)}")
        return render(request, 'orders.html', {'error': str(e)})