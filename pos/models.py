from django.db import models
from django.utils import timezone

# --- 1. Menu Management ---
class Category(models.Model):
    name = models.CharField(max_length=100)  # e.g., "Sajji", "BBQ"

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"

class MenuItem(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # Allows uploading an image for each dish
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.price}"

# --- 2. Restaurant Operations ---
class Table(models.Model):
    name = models.CharField(max_length=50, unique=True) # e.g., "Table 1"
    status = models.CharField(max_length=20, default='available', choices=[
        ('available', 'Available'),
        ('occupied', 'Occupied'),
    ])

    def __str__(self):
        return self.name

# --- 3. Order Logic ---
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('cooking', 'Sent to Kitchen'),
        ('ready', 'Ready'),
        ('completed', 'Completed/Paid'),
    ]

    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Order #{self.id} ({self.status})"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2) # Price at time of order

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name}"

    @property
    def total_price(self):
        return self.quantity * self.price
