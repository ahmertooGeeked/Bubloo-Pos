import json
from datetime import date
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .models import Category, MenuItem, Table, Order, OrderItem

# --- 1. AUTHENTICATION & SECURITY (Day 7) ---

def custom_login(request):
    """
    Renders the branded login page and handles authentication.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid username or password'})

    # If user is already logged in, redirect to POS
    if request.user.is_authenticated:
        return redirect('pos_dashboard')

    return render(request, 'pos/login.html')

def user_logout(request):
    """
    Logs the user out and sends them back to the login screen.
    """
    logout(request)
    return redirect('login')


# --- 2. POS DASHBOARD (Day 2 & 3) ---

@login_required(login_url='/login/')
def pos_dashboard(request):
    """
    Main POS View: Shows Categories, Menu Items, and Cart.
    """
    categories = Category.objects.all()
    menu_items = MenuItem.objects.filter(is_available=True)
    tables = Table.objects.all()

    context = {
        'categories': categories,
        'menu_items': menu_items,
        'tables': tables,
    }
    return render(request, 'pos/index.html', context)


# --- 3. PLACE ORDER API (Day 4) ---

@csrf_exempt
def place_order(request):
    """
    API: Receives JSON cart data, creates an Order, and marks Table as occupied.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            table_id = data.get('table_id')
            cart = data.get('cart')

            if not table_id or not cart:
                return JsonResponse({'status': 'error', 'message': 'Missing table or cart data'}, status=400)

            # Get Table
            try:
                table = Table.objects.get(id=table_id)
            except Table.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Table not found'}, status=404)

            # Mark Table as Occupied
            table.status = 'occupied'
            table.save()

            # Create Order
            order = Order.objects.create(
                table=table,
                status='pending',
                total_amount=0
            )

            # Save Items
            total = 0
            for item in cart:
                try:
                    menu_item = MenuItem.objects.get(id=item['id'])
                    quantity = int(item['quantity'])
                    price = menu_item.price

                    OrderItem.objects.create(
                        order=order,
                        menu_item=menu_item,
                        quantity=quantity,
                        price=price
                    )
                    total += (price * quantity)
                except MenuItem.DoesNotExist:
                    continue

            # Save Total
            order.total_amount = total
            order.save()

            return JsonResponse({'status': 'success', 'order_id': order.id})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


# --- 4. KITCHEN DISPLAY SYSTEM (Day 5) ---

@login_required(login_url='/login/')
def kitchen_dashboard(request):
    """
    Shows 'pending' orders for the Chef. Auto-refreshes.
    """
    pending_orders = Order.objects.filter(status='pending').order_by('created_at').prefetch_related('items__menu_item')
    return render(request, 'pos/kitchen.html', {'orders': pending_orders})

def update_order_status(request, order_id, new_status):
    """
    API: Updates order status (e.g., pending -> ready).
    """
    try:
        order = Order.objects.get(id=order_id)
        order.status = new_status
        order.save()
        return JsonResponse({'status': 'success'})
    except Order.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Order not found'}, status=404)


# --- 5. TABLE MANAGEMENT & FLOOR PLAN (Day 6) ---

@login_required(login_url='/login/')
def table_dashboard(request):
    """
    Shows Visual Floor Plan (Red/Green tables).
    """
    tables = Table.objects.all()
    tables_data = []

    for table in tables:
        active_order = None
        if table.status == 'occupied':
            # Get the current active bill
            active_order = Order.objects.filter(table=table, status__in=['pending', 'ready']).last()

        tables_data.append({
            'obj': table,
            'active_order': active_order
        })

    return render(request, 'pos/tables.html', {'tables': tables_data})

def checkout_table(request, table_id):
    """
    API: Marks a table as 'available' and the order as 'completed' (paid).
    """
    try:
        table = Table.objects.get(id=table_id)

        if table.status == 'occupied':
            # Find active order
            order = Order.objects.filter(table=table, status__in=['pending', 'ready']).last()

            if order:
                order.status = 'completed'
                order.save()

            # Free the table
            table.status = 'available'
            table.save()

            return JsonResponse({'status': 'success'})

    except Table.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Table not found'}, status=404)

    return JsonResponse({'status': 'error', 'message': 'Table is not occupied'}, status=400)


# --- 6. SALES REPORT (Day 7) ---

@login_required(login_url='/login/')
def sales_dashboard(request):
    """
    Shows total sales and order count for TODAY.
    """
    today = date.today()

    # Get only completed orders from today
    todays_orders = Order.objects.filter(
        created_at__date=today,
        status='completed'
    ).order_by('-created_at')

    # Calculate sum
    total_sales = todays_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    order_count = todays_orders.count()

    context = {
        'total_sales': total_sales,
        'order_count': order_count,
        'orders': todays_orders
    }
    return render(request, 'pos/report.html', context)
