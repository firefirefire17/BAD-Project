from django.db import models
from django.db.models.functions import Now

# Create your models here.
# https://docs.djangoproject.com/en/5.0/topics/db/models/  Extra fields on many-to-many relationships
# 


class Material(models.Model):
    name = models.CharField(max_length=50)
    stock = models.IntegerField()
    cost = models.FloatField()
    type = models.CharField(max_length=50)
    markup = models.FloatField()
    unit = models.CharField(max_length=15)
    total_value = models.FloatField(null=True, blank=True)
    
    def __str__(self):
        return str(self.name)
    
class Product(models.Model):
    name = models.CharField(max_length=50)
    stock = models.IntegerField()
    cost = models.IntegerField(null=True, blank=True)
    materials = models.ManyToManyField(Material, through='Product_Material')
    
    def __str__(self):
        return str(self.name)

class Product_Material(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    quantity = models.IntegerField()

    def __str__(self):
        return f'{self.material.name} in {self.product.name}'


class Customer(models.Model):  # currently unused
    name = models.CharField(max_length=50)
    mobile_number = models.IntegerField()

    def __str__(self):
        return str(self.name)

    
class Order(models.Model):
    customer = models.CharField(max_length=50)
    purchase_mode = models.CharField(max_length=50)
    payment_type = models.CharField(max_length=50)
    order_status = models.CharField(max_length=50, default="In-queue")
    order_date = models.DateField()
    delivery_date = models.DateField()
    order_price = models.FloatField(null=True, blank=True)
    address_city = models.CharField(max_length=50)
    address_street = models.CharField(max_length=50)
    address_barangay = models.CharField(max_length=50)
    address_zip = models.IntegerField()
    contact_number = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f'{self.customer}_{self.order_date}'
    
class Item(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    type = models.CharField(max_length=50)
    cost = models.FloatField(null=True, blank=True)
    materials = models.ManyToManyField(Material, through='Item_Material')

class Item_Material(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    quantity = models.IntegerField()

    def __str__(self):
        return f'{self.material.name} in Item #{self.item.pk}'

class Order_Item(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField()

    def __str__(self):
        return f'{self.item.pk} in Order #{self.order.pk}'
    






