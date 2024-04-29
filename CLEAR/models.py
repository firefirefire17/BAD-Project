from django.db import models
from django.db.models.functions import Now
from django.core.validators import MinValueValidator, MaxValueValidator, MaxLengthValidator

# Create your models here.
# https://docs.djangoproject.com/en/5.0/topics/db/models/  Extra fields on many-to-many relationships
# 

class MaterialKey(models.Model):
    material_key = models.AutoField(primary_key=True)

class Textile(models.Model):
    TEXTILE_UNIT_CHOICES = [
        ("FT", "per sq/ft"),
        ("IN", "per sq/in"),
        ("M", "per sq/m"),
    ]
    name = models.CharField(max_length=50, validators=[MaxLengthValidator(50)])
    cost = models.FloatField()
    unit = models.CharField(max_length=2, choices = TEXTILE_UNIT_CHOICES, default="FT")
    stock = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(999)])
    material_key = models.OneToOneField(MaterialKey, on_delete=models.CASCADE)

class Accessory(models.Model):
    ACCESSORY_UNIT_CHOICES = [
        ("PC", "per piece"),
        ("IN", "per inch"),
    ]
    name = models.CharField(max_length=50, validators=[MaxLengthValidator(50)])
    cost = models.FloatField()
    unit = models.CharField(max_length=2, choices = ACCESSORY_UNIT_CHOICES, default="PC")
    stock = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(999)])
    material_key = models.OneToOneField(MaterialKey, on_delete=models.CASCADE)
    
class Product(models.Model):
    name = models.CharField(max_length=50)
    stock = models.IntegerField()
    prod_margin = models.FloatField(null=True) # renamed from 'margin'
    labor_time = models.IntegerField(null=True) 
    misc_margin = models.IntegerField(null=True)
    calc_price = models.FloatField(null=True) # renamed from 'total_cost'
    retail_price = models.FloatField(null=True)
    last_update = models.DateField(null=True) # remove null once views has been finalized

    textiles = models.ManyToManyField(Textile, through='Product_Component')
    accessories = models.ManyToManyField(Accessory, through='Product_Accessory')
    
    def __str__(self):
        return str(self.name)
    
    def updateCost(self):
        print("pass")
        wage_object = Global_Value.objects.get(name="labor_wage")
        wage = wage_object.value
        
        vat_object = Global_Value.objects.get(name="vat")
        vat = vat_object.value

        print(wage)
        print(vat)

        labor_time = self.labor_time
        prod_margin = self.prod_margin
        misc_margin = self.misc_margin

        raw_material_cost = 0
        for product_component in self.product_component_set.all():
            height = product_component.height
            width = product_component.width
            quantity = product_component.quantity
            textile_cost = product_component.textile.cost
            textile_unit = product_component.textile.unit
            print(product_component.buffer)
            buffer = product_component.buffer

            productComponent_cost = get_prodComponentCost(height, width, quantity, textile_unit, textile_cost, buffer)
            raw_material_cost += productComponent_cost
            print(f"product component: {productComponent_cost}")
        
        for product_accessory in self.product_accessory_set.all():
            quantity = product_accessory.accessory_quantity
            accessory_cost = product_accessory.accessory.cost
            productAccessory_cost = quantity*accessory_cost
            raw_material_cost += productAccessory_cost
            print(f"product accessory: {productAccessory_cost}")

        labor_cost = wage*(int(labor_time)/60)
        total_cost = raw_material_cost + labor_cost + labor_cost*(float(misc_margin)/100)
        margin = total_cost*(float(prod_margin)/100)
        calc_price = (total_cost + margin)*(1 + (vat/100))
        self.calc_price = calc_price

        print(f"labor: {labor_cost}")
        print(f"total cost: {total_cost}")
        print(f"margin: {margin}")

        print(calc_price)
        return self.calc_price





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
    buffer = models.FloatField(null=True)  

    
class Job_Order(models.Model):
    order_status = models.CharField(max_length=50, default="In-queue")
    file_date = models.DateField()
    start_date = models.DateField(null=True)
    completion_date = models.DateField(null=True)
    customer = models.CharField(max_length=50, null=True)

    def __str__(self):
        return f'{self.pk}_{self.file_date}'
    
class Store(models.Model):
    store_name = models.CharField(max_length=50)
    job_order = models.ForeignKey(Job_Order, on_delete=models.CASCADE)
    
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
        return f'{self.accessory.name} in Item #{self.item.pk}'

class Order_Item(models.Model):
    order = models.ForeignKey(Job_Order, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField()

    def __str__(self):
        return f'{self.item.pk} in Order #{self.order.pk}'

class StockIn(models.Model):
    transaction_date = models.DateField()
    edit_reason  = models.CharField(max_length=200, null=True)
    accessories = models.ManyToManyField(Accessory, through="StockIn_Accessory")
    textiles = models.ManyToManyField(Textile, through="StockIn_Textile")
    total_cost = models.FloatField(null=True)

    def updateCost(self):
        total_cost = 0
        textiles = self.stockin_textile_set.all()
        accessories = self.stockin_accessory_set.all()
        for stock_textile in textiles:
                quantity = stock_textile.quantity
                cost = stock_textile.cost
                total_cost += (quantity*cost)
        for stock_accessory in accessories:
                quantity = stock_accessory.quantity
                cost = stock_accessory.cost
                total_cost += (quantity*cost)
        self.total_cost = total_cost

class StockIn_Accessory(models.Model):
    accessory = models.ForeignKey(Accessory, on_delete=models.CASCADE)
    stock_in = models.ForeignKey(StockIn, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    cost = models.FloatField()

class StockIn_Textile(models.Model):
    textile = models.ForeignKey(Textile, on_delete=models.CASCADE)
    stock_in = models.ForeignKey(StockIn, on_delete=models.CASCADE)
    quantity = models.FloatField()
    cost = models.FloatField()
    

class Global_Value(models.Model):
    name = models.CharField(max_length=50)
    value = models.IntegerField()

class Account(models.Model):
    username = models.CharField(max_length=50)
    password = models.IntegerField()
    role = models.CharField(max_length=50)





# function used in products to get cost of a product component
def get_prodComponentCost(height, width, quantity, textile_unit, textile_cost, buffer):
    sq_inch  = float(height)*float(width)*float(buffer/100 + 1)
    if textile_unit == "FT":
        final_unit = sq_inch / 144
    elif textile_unit == "M":
        final_unit = sq_inch / 1550.0031
    else:
        final_unit = sq_inch
    
    final_quantity = final_unit*float(quantity)
    final_cost = final_quantity*float(textile_cost)
    return final_cost

