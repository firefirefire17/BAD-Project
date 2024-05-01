from django.contrib import admin
from .models import Textile, Accessory, Product, Product_Accessory, Component, Product_Component, Job_Order, Item, Item_Accessory, Item_Textile, Order_Item, StockIn, StockIn_Accessory, StockIn_Textile, Financial_Value, Account
# Register your models here.

admin.site.register(Textile)
admin.site.register(Product)
admin.site.register(Accessory)
admin.site.register(Product_Accessory)
admin.site.register(Component)
admin.site.register(Item)
admin.site.register(Product_Component)
admin.site.register(Order_Item)
admin.site.register(Job_Order)
admin.site.register(Item_Accessory)
admin.site.register(Item_Textile)
admin.site.register(StockIn)
admin.site.register(StockIn_Accessory)
admin.site.register(StockIn_Textile)
admin.site.register(Financial_Value)
admin.site.register(Account)