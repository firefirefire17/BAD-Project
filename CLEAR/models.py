from django.db import models
from django.db.models.functions import Now

# Create your models here.
# https://docs.djangoproject.com/en/5.0/topics/db/models/  Extra fields on many-to-many relationships
# 

class MaterialKey(models.Model):
    material_key = models.AutoField(primary_key=True)

class Textile(models.Model):
    TEXTILE_UNIT_CHOICES = [
        ("FT", "per sq/ft"),
        ("IN", "per inch"),
        ("M", "per meter"),
    ]
    name = models.CharField(max_length=50)
    cost = models.FloatField()
    unit = models.CharField(max_length=2, choices = TEXTILE_UNIT_CHOICES, default="FT")
    stock = models.FloatField()
    material_key = models.OneToOneField(MaterialKey, on_delete=models.CASCADE)

class Accessory(models.Model):
    ACCESSORY_UNIT_CHOICES = [
        ("PC", "per piece"),
        ("IN", "per inch"),
    ]
    name = models.CharField(max_length=50)
    cost = models.FloatField()
    unit = models.CharField(max_length=2, choices = ACCESSORY_UNIT_CHOICES, default="PC")
    stock = models.IntegerField()
    material_key = models.OneToOneField(MaterialKey, on_delete=models.CASCADE)
    
class Product(models.Model):
    # product_number = models.AutoField(primary_key=True) this thing is purely fucked up
    name = models.CharField(max_length=50)
    stock = models.IntegerField()
    prod_margin = models.FloatField() # renamed from 'margin'
    labor_time = models.IntegerField() 
    misc_margin = models.IntegerField(default=50)
    total_cost = models.FloatField(null=True) # renamed from 'cost'
    textiles = models.ManyToManyField(Textile, through='Product_Component')
    accessories = models.ManyToManyField(Accessory, through='Product_Accessory')
    
    def __str__(self):
        return str(self.name)

class Product_Accessory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    accessory = models.ForeignKey(Accessory, on_delete=models.CASCADE)
    accessory_quantity = models.IntegerField()

    def __str__(self):
        return f'{self.accessory.name} in {self.product.name}'

    
class Component(models.Model):
    component_name = models.CharField(max_length=50)

class Product_Component(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    textile = models.ForeignKey(Textile, on_delete=models.CASCADE)
    component = models.ForeignKey(Component, on_delete=models.CASCADE)
    height = models.FloatField()
    width = models.FloatField()
    quantity = models.IntegerField()
    buffer = models.FloatField()  

    
class Job_Order(models.Model):
    order_status = models.CharField(max_length=50, default="In-queue")
    file_date = models.DateField()
    completion_date = models.DateField(null=True)

    def __str__(self):
        return f'{self.pk}_{self.file_date}'
    
class Item(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, db_column='product_number')
    type = models.CharField(max_length=50)
    cost = models.FloatField(null=True)
    accessories = models.ManyToManyField(Accessory, through='Item_Accessory')
    textiles = models.ManyToManyField(Textile, through='Item_Textile')

class Item_Textile(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, db_column='product_number')
    textile = models.ForeignKey(Textile, on_delete=models.CASCADE)
    bespoke_rate = models.FloatField()
    quantity = models.IntegerField()

    def __str__(self):
        return f'{self.textile.name} in Item #{self.item.pk}'
    
class Item_Accessory(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, db_column='product_number')
    accessory = models.ForeignKey(Accessory, on_delete=models.CASCADE)
    bespoke_rate = models.FloatField()
    quantity = models.IntegerField()

    def __str__(self):
        return f'{self.textile.name} in Item #{self.item.pk}'

class Order_Item(models.Model):
    order = models.ForeignKey(Job_Order, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField()

    def __str__(self):
        return f'{self.item.pk} in Order #{self.order.pk}'

class Transaction(models.Model):
    transaction_date = models.DateField()
    edit_reason  = models.CharField(max_length=200, null=True)
    textiles = models.ManyToManyField(Textile, through='Transaction_Textile')
    accessories = models.ManyToManyField(Accessory, through='Transaction_Accessory')

class Transaction_Accessory(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    accessory = models.ForeignKey(Accessory, on_delete=models.CASCADE)
    quantity = models.IntegerField()

class Transaction_Textile(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    textile = models.ForeignKey(Textile, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    

class Global_Value(models.Model):
    name = models.CharField(max_length=50)
    value = models.IntegerField()

class Account(models.Model):
    username = models.CharField(max_length=50)
    password = models.IntegerField()
    role = models.CharField(max_length=50)







