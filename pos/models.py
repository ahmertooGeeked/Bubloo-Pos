from django.db import models
from django.utils import timezone

# --- 1. Menu Management ---
class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"

class MenuItem(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True)
    is_available = models.BooleanField(default=True)

    # NO STOCK FIELD HERE (As requested)

    def __str__(self):
        return f"{self.name} - {self.price}"

# --- 2. Restaurant Operations ---
class Table(models.Model):
    name = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, default='available', choices=[
        ('available', 'Available'),
        ('occupied', 'Occupied'),
    ])

    def __str__(self):
        return self.name

# --- 3. Order Logic ---
class Order(models.Model):
    ORDER_TYPES = (
        ('dine-in', 'Dine-in'),
        ('takeaway', 'Takeaway'),
    )

    # NEW: Payment Methods
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('online', 'Online/Wallet'),
    )

    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True)
    order_type = models.CharField(max_length=10, choices=ORDER_TYPES, default='dine-in')

    # NEW FIELD
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, default='cash')

    customer_name = models.CharField(max_length=100, blank=True, null=True)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)

    # Cash Handling
    cash_given = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    change_due = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    status = models.CharField(max_length=20, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} ({self.payment_method})"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name}"

    @property
    def total_price(self):
        return self.quantity * self.price

# --- 4. SHIFT MANAGEMENT ---
class Shift(models.Model):
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)

    opening_cash = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Financials (Calculated at closing)
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # The comparison
    calculated_cash = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    actual_cash = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    difference = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Shift #{self.id} - {self.start_time.strftime('%d/%m %H:%M')}"

class Expense(models.Model):
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='expenses')
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.description}: {self.amount}"
