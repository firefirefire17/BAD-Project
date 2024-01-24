from django.contrib import admin
from .models import Material, Product, Product_Material, Order, Customer, Item, Item_Material, Order_Item 
# Register your models here.

admin.site.register(Material)
admin.site.register(Product)
admin.site.register(Product_Material)
admin.site.register(Order)
admin.site.register(Customer)
admin.site.register(Item)
admin.site.register(Item_Material)
admin.site.register(Order_Item)