from datetime import datetime
import json
from decimal import Decimal
from django.utils import timezone
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F
from .models import Category, MenuItem, Table, Order, OrderItem, Shift, Expense

# --- 1. AUTHENTICATION ---
def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid credentials'})
    if request.user.is_authenticated:
        return redirect('pos_dashboard')
    return render(request, 'pos/login.html')

def user_logout(request):
    logout(request)
    return redirect('login')

# --- 2. POS DASHBOARD ---
@login_required(login_url='/login/')
def pos_dashboard(request):
    categories = Category.objects.all()
    menu_items = MenuItem.objects.filter(is_available=True)
    tables = Table.objects.all()
    return render(request, 'pos/index.html', {
        'categories': categories,
        'menu_items': menu_items,
        'tables': tables,
    })

# --- 3. PLACE ORDER API ---
@csrf_exempt
def place_order(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cart = data.get('cart')
            order_type = data.get('order_type')
            payment_method = data.get('payment_method', 'cash')

            customer_name = data.get('customer_name', '')
            customer_phone = data.get('customer_phone', '')

            cash_given_str = data.get('cash_given', '0')
            if not cash_given_str: cash_given_str = '0'
            cash_given = Decimal(str(cash_given_str))

            if not cart:
                return JsonResponse({'status': 'error', 'message': 'Cart is empty'}, status=400)

            # Table Logic
            table = None
            if order_type == 'dine-in':
                table_id = data.get('table_id')
                if not table_id:
                    return JsonResponse({'status': 'error', 'message': 'Table required'}, status=400)
                try:
                    table = Table.objects.get(id=table_id)
                    table.status = 'occupied'
                    table.save()
                except Table.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Table not found'}, status=404)

            # Takeaway Check
            if order_type == 'takeaway' and not customer_name:
                return JsonResponse({'status': 'error', 'message': 'Name required for Takeaway'}, status=400)

            # Create Order
            order = Order.objects.create(
                table=table,
                order_type=order_type,
                payment_method=payment_method,
                customer_name=customer_name,
                customer_phone=customer_phone,
                cash_given=cash_given,
                status='pending',
                total_amount=0
            )

            # Save Items
            total = Decimal('0.00')
            for item in cart:
                try:
                    menu_item = MenuItem.objects.get(id=item['id'])
                    quantity = int(item['quantity'])
                    price = menu_item.price
                    OrderItem.objects.create(order=order, menu_item=menu_item, quantity=quantity, price=price)
                    total += (price * quantity)
                except MenuItem.DoesNotExist:
                    continue

            order.total_amount = total

            # Calculate Change
            if payment_method == 'cash':
                if cash_given >= total:
                    order.change_due = cash_given - total
                else:
                    order.change_due = Decimal('0.00')
            else:
                order.change_due = Decimal('0.00')
                order.cash_given = total

            order.save()
            return JsonResponse({'status': 'success', 'order_id': order.id})

        except Exception as e:
            print(f"Error in place_order: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

# --- 4. SUCCESS PAGE ---
@login_required(login_url='/login/')
def order_success(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        return render(request, 'pos/success.html', {'order': order})
    except Order.DoesNotExist:
        return redirect('pos_dashboard')

# --- 5. KITCHEN ---
@login_required(login_url='/login/')
def kitchen_dashboard(request):
    pending_orders = Order.objects.filter(status='pending').order_by('created_at').prefetch_related('items__menu_item')
    return render(request, 'pos/kitchen.html', {'orders': pending_orders})

def update_order_status(request, order_id, new_status):
    try:
        order = Order.objects.get(id=order_id)
        order.status = new_status
        order.save()
        return JsonResponse({'status': 'success'})
    except Order.DoesNotExist:
        return JsonResponse({'status': 'error'}, status=404)

# --- 6. MANAGER ---
@login_required(login_url='/login/')
def table_dashboard(request):
    tables = Table.objects.all()
    tables_data = []
    for table in tables:
        active_order = None
        if table.status == 'occupied':
            active_order = Order.objects.filter(table=table, status__in=['pending', 'ready']).last()
        tables_data.append({'obj': table, 'active_order': active_order})

    active_takeaways = Order.objects.filter(order_type='takeaway', status__in=['pending', 'ready']).order_by('-created_at')
    return render(request, 'pos/tables.html', {'tables': tables_data, 'takeaways': active_takeaways})

def checkout_table(request, table_id):
    try:
        table = Table.objects.get(id=table_id)
        if table.status == 'occupied':
            order = Order.objects.filter(table=table, status__in=['pending', 'ready']).last()
            if order:
                order.status = 'completed'
                order.save()
            table.status = 'available'
            table.save()
            return JsonResponse({'status': 'success'})
    except Table.DoesNotExist:
        return JsonResponse({'status': 'error'}, status=404)
    return JsonResponse({'status': 'error'}, status=400)

def settle_order(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        order.status = 'completed'
        order.save()
        return JsonResponse({'status': 'success'})
    except Order.DoesNotExist:
        return JsonResponse({'status': 'error'}, status=404)

# --- 7. REPORTS (UPDATED TO SHOW CANCELLED ORDERS) ---
@login_required(login_url='/login/')
def sales_dashboard(request):
    # 1. Date Logic
    date_str = request.GET.get('date')
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            target_date = timezone.now().date()
    else:
        target_date = timezone.now().date()

    # 2. Filter Orders: Get ALL orders for the date (Completed AND Cancelled), exclude Pending
    orders = Order.objects.filter(
        created_at__date=target_date
    ).exclude(status='pending').order_by('-created_at')

    # 3. Calculate Totals (ONLY from Completed orders)
    # We filter specifically for 'completed' here so Void orders don't add money
    completed_orders = orders.filter(status='completed')

    total_sales = completed_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    order_count = completed_orders.count()

    return render(request, 'pos/report.html', {
        'total_sales': total_sales,
        'order_count': order_count,
        'orders': orders, # Sends ALL orders (including void) to the list
        'selected_date': target_date
    })

def generate_bill(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        return render(request, 'pos/bill.html', {'order': order})
    except Order.DoesNotExist:
        return HttpResponse("Order not found", status=404)

# --- 8. SHIFT MANAGEMENT ---
@login_required(login_url='/login/')
def shift_dashboard(request):
    active_shift = Shift.objects.filter(is_active=True).last()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'start_shift':
            opening_cash = Decimal(request.POST.get('opening_cash', '0'))
            Shift.objects.create(opening_cash=opening_cash, is_active=True)
            return redirect('shift_dashboard')

        elif action == 'add_expense' and active_shift:
            desc = request.POST.get('description')
            amount = Decimal(request.POST.get('amount', '0'))
            Expense.objects.create(shift=active_shift, description=desc, amount=amount)
            return redirect('shift_dashboard')

        elif action == 'close_shift' and active_shift:
            actual_cash = Decimal(request.POST.get('actual_cash', '0'))
            orders = Order.objects.filter(created_at__gte=active_shift.start_time, status='completed')
            total_sales = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0')
            expenses = Expense.objects.filter(shift=active_shift)
            total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
            calculated_cash = active_shift.opening_cash + total_sales - total_expenses
            difference = actual_cash - calculated_cash

            active_shift.end_time = timezone.now()
            active_shift.total_sales = total_sales
            active_shift.total_expenses = total_expenses
            active_shift.calculated_cash = calculated_cash
            active_shift.actual_cash = actual_cash
            active_shift.difference = difference
            active_shift.is_active = False
            active_shift.save()
            return redirect('shift_dashboard')

    context = {}
    if active_shift:
        orders = Order.objects.filter(created_at__gte=active_shift.start_time, status='completed')
        current_sales = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0')
        expenses = Expense.objects.filter(shift=active_shift)
        current_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        expected_cash = active_shift.opening_cash + current_sales - current_expenses
        context = {
            'shift': active_shift,
            'current_sales': current_sales,
            'current_expenses': current_expenses,
            'expected_cash': expected_cash,
            'expenses': expenses
        }
    else:
        recent_shifts = Shift.objects.filter(is_active=False).order_by('-end_time')[:5]
        context['recent_shifts'] = recent_shifts

    return render(request, 'pos/shift.html', context)

# --- 9. DIGITAL BILL ---
def digital_bill(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        return render(request, 'pos/digital_bill.html', {'order': order})
    except Order.DoesNotExist:
        return HttpResponse("Invoice not found", status=404)

# --- 10. CANCEL ORDER ---
def cancel_order(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        order.status = 'cancelled'
        order.save()
        if order.table:
            order.table.status = 'available'
            order.table.save()
        return JsonResponse({'status': 'success'})
    except Order.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Order not found'}, status=404)
