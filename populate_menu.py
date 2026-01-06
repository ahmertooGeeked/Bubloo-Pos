import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from pos.models import Category, MenuItem, Table

# 1. Create Tables
print("Creating Tables...")
for i in range(1, 11):
    Table.objects.get_or_create(name=f"Table {i}")

# 2. Create Categories
print("Creating Categories...")
cat_sajji, _ = Category.objects.get_or_create(name="Chicken Sajji With Rice")
cat_bbq, _ = Category.objects.get_or_create(name="B.B.Q")
cat_platter, _ = Category.objects.get_or_create(name="B.B.Q Platter")
cat_salad, _ = Category.objects.get_or_create(name="Salad")
cat_drinks, _ = Category.objects.get_or_create(name="Drinks")

# 3. Create Menu Items
print("Populating Menu...")
items = [
    # Sajji
    (cat_sajji, "Chicken Sajji Arabic Full", 2300),
    (cat_sajji, "Chicken Sajji Arabic Half", 1199),
    (cat_sajji, "Chicken Sajji Peri Peri Full", 2300),
    (cat_sajji, "Chicken Sajji Peri Peri Half", 1199),
    (cat_sajji, "Chicken Sajji Quater Chest", 650),
    (cat_sajji, "Chicken Sajji Quater Leg", 590),
    (cat_sajji, "Plain Rice", 300),

    # B.B.Q
    (cat_bbq, "Malai Boti (10Pcs)", 999),
    (cat_bbq, "Chicken Boti (10Pcs)", 890),
    (cat_bbq, "Chicken Kabab (4Pcs)", 890),
    (cat_bbq, "Kalmi Tikka (4Pcs)", 850),
    (cat_bbq, "Beef Kabab (4Pcs)", 950),
    (cat_bbq, "Fish Tikka (10Pcs)", 999),

    # Platters
    (cat_platter, "2-3 Persons Platter", 2949),
    (cat_platter, "4-5 Persons Platter", 5299),
    (cat_platter, "Bubloo Special Platter", 7499),

    # Salad
    (cat_salad, "Hummus", 499),
    (cat_salad, "Fattoush Salad", 350),
    (cat_salad, "Green Salad", 150),
    (cat_salad, "Mint Raita", 100),

    # Drinks
    (cat_drinks, "Cold Drink 1.5Ltr", 220),
    (cat_drinks, "Pepsi Can", 120),
    (cat_drinks, "Mineral Water Large", 120),
]

for cat, name, price in items:
    MenuItem.objects.get_or_create(category=cat, name=name, price=price)

print("✅ Success! Database populated with Bubloo Ki Sajji menu.")
