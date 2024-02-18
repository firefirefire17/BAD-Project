from django.shortcuts import render, redirect, get_object_or_404
from .models import Textile, Accessory, Product, Product_Accessory, Component, Product_Component, Job_Order, Item, Item_Accessory, Item_Textile, Order_Item, Transaction, Transaction_Accessory, Transaction_Textile, Global_Value, Account, MaterialKey
from django.contrib.auth import authenticate, login, logout
from .forms import RegisterForm, LoginForm
from django.contrib.auth.decorators import login_required



# Create your views here.

@login_required(login_url="/login") # this is to restrict access if not logged in
def dashboard(request):
    return render(request, 'CLEAR/dashboard.html')

#new products
@login_required(login_url="/login")
def products(request):
    product_objects = Product.objects.all()
    accessory_objects = Accessory.objects.all()
    textile_objects = Textile.objects.all()

    product_material_list = []

    #create a list of dicts
    for product in product_objects:
        data = {
            'product':product,
            'component':product.product_component_set.all(),
            'accessories':product.product_accessory_set.all()
        }
        product_material_list.append(data)

    if request.method == "POST":
        if 'add_product_form' in request.POST:
            #adding of stuff
            name = request.POST.get("name")
            stock = request.POST.get("stock")
            prod_margin = request.POST.get("prod_margin")
            labor_time = request.POST.get("labor_time")
            misc_margin = request.POST.get("misc_margin")
            total_cost = request.POST.get("total_cost")
            textiles_ids = request.POST.getlist("textiles")
            accessories_ids = request.POST.getlist("accessories")

            #create new product
            new_product = Product.objects.create(name=name, 
                                                 stock=stock, 
                                                 prod_margin=prod_margin, 
                                                 labor_time=labor_time, 
                                                 misc_margin=misc_margin, 
                                                 total_cost=total_cost)

            #add textiles
            for textile_id in textiles_ids:
                textile = Textile.objects.get(pk=textile_id)
                new_product.textiles.add(textile)

            #add textiles alt
            '''
            for textile_id in textiles_ids:
                textile = Textile.objects.get(pk=textile_id)
                <We Dont Have a Product_Textile Assoc Entity>.objects.create(product=add_product, textile=textile)
            '''

            #add accs old
            '''
            for accessory_id in accessories_ids:
                accessory = Accessory.objects.get(pk=accessory_id)
                new_product.accessories.add(accessory)
            '''

            #add accs
            for accessory_id in accessories_ids:
                accessory = Accessory.objects.get(pk=accessory_id)
                Product_Accessory.objects.create(product=new_product, accessory=accessory)

            return redirect("products")

        elif 'edit_form' in request.POST:
            #edit of stuff
            product_pk = request.POST.get("product_pk")
            accessory_pk = request.POST.get("accessory_pk")
            quantity = request.POST.get("accessory_quantity")
            product = get_object_or_404(Product, pk=product_pk)
            accessory = get_object_or_404(Product_Accessory, product=product, accessory__pk=accessory_pk)

            #update acc qty field
            accessory.accessory_quantity = quantity
            accessory.save()
            
            #update fields
            product.name = request.POST.get("name")
            product.stock = request.POST.get("stock")
            product.labor_time = request.POST.get("labor_time")
            product.misc_margin = request.POST.get("misc_margin")
            
            product.save()

            return redirect('products')

        elif 'delete_form' in request.POST:
            #delete
            product.pk = request.POST.get("productMaterial_pk")
            Product.objects.filter(pk=product_pk).delete()

            return redirect('products')
        
    return render(request, 'CLEAR/products.html', {'products':product_objects, 
                                                   'product_material_list':product_material_list,
                                                   'accessories':accessory_objects,
                                                   'textiles':textile_objects})

# orders used to be here

@login_required(login_url="/login")
def materials(request):
    textile_objects = Textile.objects.all()
    accessory_objects = Accessory.objects.all()
    material_objects = []

    for textile in textile_objects:
        material_objects.append({'type': 'textile', 'material': textile, 'unit': textile.get_unit_display()})

    for accessory in accessory_objects:
        material_objects.append({'type': 'accessory', 'material': accessory, 'unit': accessory.get_unit_display()})

    print(material_objects)

    if(request.method=="POST"):
        material_key = request.POST.get("material_key")
        type = request.POST.get("type")

        if "add_form" in request.POST:
            name = request.POST.get("name")
            stock = float(request.POST.get("stock"))
            cost = request.POST.get("cost")
            material_key = MaterialKey.objects.create()
            print(material_key)
            if type == "textile": 
                Textile.objects.create(name=name, stock=stock, cost=cost, material_key=material_key)
            if type == "accessory":
                Accessory.objects.create(name=name, stock=stock, cost=cost, material_key=material_key)
            return redirect('materials')

        elif "edit_form" in request.POST:
            name = request.POST.get("name")
            stock = float(request.POST.get("stock"))
            cost = request.POST.get("cost")
            material_key_obj = get_object_or_404(MaterialKey, material_key=material_key)
            if type == "textile":
                print(material_key_obj)
                Textile.objects.filter(material_key=material_key_obj).update(name=name, stock=stock, cost=cost)
            else:
                print(material_key_obj)
                Accessory.objects.filter(material_key=material_key_obj).update(name=name, stock=stock, cost=cost)
            return redirect('materials')

        elif "delete_form" in request.POST:
            material_key_obj = get_object_or_404(MaterialKey, material_key=material_key)
            print(material_key_obj)
            if type == "textile":
                Textile.objects.filter(material_key=material_key_obj).delete()
            if type == "accessory":
                Accessory.objects.filter(material_key=material_key_obj).delete()
            return redirect('materials')


    return render(request, 'CLEAR/materials.html', {'materials':material_objects})

@login_required(login_url="/login")
def reports(request):
    return render(request, 'CLEAR/reports.html')


def sign_up(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')

    else:
        form = RegisterForm()

    return render(request, 'registration/sign_up.html', {"form": form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
    else:
        form = LoginForm()

    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')


''' old def products()
def products(request):
    product_objects = Product.objects.all()
    accessory_objects = Accessory.objects.all()
    textile_objects = Textile.objects.all()


    product_material_list = []

    # create a list of dictionaries, each dictionary pertaining to one product and its associated information
    for product in product_objects:
        data = {
            'product': product,
            'component': product.product_component_set.all(),
            'accessories': product.product_accessory_set.all()
        }
        product_material_list.append(data)
    
    if(request.method=="POST"):
            name = request.POST.get("name")
            stock = request.POST.get("stock")
            prod_margin = request.POST.get("prod_margin")
            labor_time = request.POST.get("labor_time")
            misc_margin = request.POST.get("misc_margin")

        print(request.POST)
        
        if 'edit_form' in request.POST:
            product_pk = request.POST.get("product_pk")
            product = get_object_or_404(Product, pk=product_pk)

            x = 1
            while True:
                pass # leave it for now
            Product.objects.filter(pk=product_pk).update(stock=stock, name=name)
            return redirect('products')

        elif 'delete_form' in request.POST:
            product_pk = request.POST.get("productMaterial_pk")
            Product.objects.filter(pk=product_pk).delete()
            return redirect('products')
        
        elif 'add_form' in request.POST:
            #create product
            new_product = Product.objects.create(stock=stock, name=name)

            #create product_materials
            x = 1
            while True:
                pass
            new_product.cost = product_cost
            new_product.save()
            return redirect('products')

    return render(request, 'CLEAR/products.html', {'products':product_objects, 'product_materials_list':product_material_list, 'accessories':accessory_objects, 'textiles':textile_objects})
'''


'''
def orders(request):
    order_objects = Order.objects.all()
    customer_objects = Customer.objects.all()
    material_objects = Material.objects.all()
    product_objects = Product.objects.all()
    product_names = {} 
    order_list = []

    # create a list of product names, currently unused
    for product in product_objects: 
        product_names[product.pk] = product.name

    # create a list of dictionaries, each dictionary containing an order and its associated list of items
        # each entry in the list of items is a dictionary containing the information of each item
    for order in order_objects:
        order_data = {
            'order': order,
            'items': []
        }
        for order_item in order.order_item_set.all():
            item_data = {
                'item': order_item,
                'materials': [],
                'product': order_item.item.product,
                'type': order_item.item.type
            }
            for item_material in order_item.item.item_material_set.all():
                material_data = {
                    'item_material': item_material,
                    'material': item_material.material,
                    'quantity': item_material.quantity,
                    'unit': item_material.material.unit
                }
                item_data['materials'].append(material_data)
            order_data['items'].append(item_data)
        order_list.append(order_data)
        

    if(request.method=="POST"):
        # customer_pk = request.POST.get("customer_pk")
        customer_name = request.POST.get("customer_name")
        customer_number = request.POST.get("customer_number")
        payment_type = request.POST.get("payment_type")
        purchase_mode = request.POST.get("purchase_mode")
        order_status = request.POST.get("order_status")
        delivery_date = request.POST.get("delivery_date")
        order_date = request.POST.get("order_date")

        address_street = request.POST.get("address_street")
        address_barangay = request.POST.get("address_barangay")
        address_city = request.POST.get("address_city")
        address_zip = request.POST.get("address_zip")

        order_pk = request.POST.get("order_pk")

        if 'add_form' in request.POST:

            new_order = Order.objects.create(customer=customer_name, contact_number=customer_number, purchase_mode=purchase_mode, payment_type=payment_type, order_status=order_status, order_date=order_date, delivery_date=delivery_date, address_city=address_city, address_street=address_street, address_barangay=address_barangay, address_zip=address_zip)
            
            x = 1
            order_price = 0 
            while True:
                item_number = request.POST.get(f"order_item_number{x}")
                item_productPK = request.POST.get(f"item_productPK{x}")
                item_type = request.POST.get(f"item_type{x}")
                item_quantity = request.POST.get(f"item_quantity{x}")
                
                item_price = 0

                if item_number is None:
                    break
                else:
                    if item_productPK == "delete":
                        pass
                    else:
                        item_product = get_object_or_404(Product, pk = item_productPK)
                        new_item = Item.objects.create(product=item_product, type=item_type)
                        order_item = Order_Item.objects.create(order=new_order, item=new_item, quantity=item_quantity)
                        
                        # add the cost of each product in an item
                        item_price += float(item_product.cost)
                    
                        y = 1
                        while True:
                            item_material_materialPK = request.POST.get(f"{x}_item_material_materialPK{y}")
                            item_material_quantity = request.POST.get(f"{x}_item_material_quantity{y}")

                            if item_material_materialPK is None:
                                break
                            else:
                                if item_material_materialPK == "delete":
                                    pass
                                else:
                                    item_material_material = get_object_or_404(Material, pk = item_material_materialPK)
                                    item_material = Item_Material.objects.create(item=new_item, quantity=item_material_quantity, material=item_material_material)

                                    # add the cost of each additional material
                                    item_price += item_material.material.cost*int(item_material.quantity)*item_material.material.markup
                            y += 1

                # multiply the price of item_product + item_materials by item quantity, then add to order_price
                item_price = item_price * int(order_item.quantity)
                order_price += item_price
                x += 1

            new_order.order_price = order_price
            new_order.save()
            return redirect('orders')
        
        elif 'edit_form' in request.POST:

            Order.objects.filter(pk=order_pk).update(customer=customer_name, contact_number=customer_number, purchase_mode=purchase_mode, payment_type=payment_type, order_status=order_status, order_date=order_date, delivery_date=delivery_date, address_city=address_city, address_street=address_street, address_barangay=address_barangay, address_zip=address_zip)
            order = Order.objects.filter(pk=order_pk).get()
            
            x = 1
            order_price = 0
            while True:
                item_number = request.POST.get(f'order_item_number{x}')
                item_pk = request.POST.get(f'hidden_item_pk{x}')
                order_item_pk = request.POST.get(f'hidden_order_item_pk{x}')
                item_productPK = request.POST.get(f"{order_pk}item_productPK{x}")
                item_type = request.POST.get(f"item_type{x}")
                item_quantity = request.POST.get(f"item_quantity{x}")

                item_price = 0

                if item_number is None:
                    break
                else:
                    if item_productPK == "delete":
                        order_item = Order_Item.objects.filter(pk=order_item_pk).delete()
                    else:
                        item_product = get_object_or_404(Product, pk=item_productPK)
                        Item.objects.filter(pk=item_pk).update(product=item_product, type=item_type)
                        Order_Item.objects.filter(pk=order_item_pk).update(quantity=item_quantity)
                        order_item = Order_Item.objects.get(pk=order_item_pk)

                        item_price += item_product.cost

                        y = 1
                        while True:
                            item_material_number = request.POST.get(f"{x}_item_material_number{y}")
                            item_materialPK = request.POST.get(f"{x}_item_materialPK{y}")
                            item_material_materialPK = request.POST.get(f"{order_pk}_{x}_item_material_materialPK{y}")
                            item_material_quantity = request.POST.get(f"{x}_item_material_quantity{y}")

                            if item_material_number is None:
                                break
                            else:
                                if item_material_materialPK == "delete":
                                    item_material = Item_Material.objects.filter(pk=item_materialPK).delete()
                                else:
                                    item_material_material = get_object_or_404(Material, pk=item_material_materialPK)
                                    Item_Material.objects.filter(pk=item_materialPK).update(quantity=item_material_quantity, material=item_material_material)
                                    item_material = Item_Material.objects.get(pk=item_materialPK)

                                    item_price += item_material.material.cost*int(item_material.quantity)*item_material.material.markup

                            y += 1
                            
                item_price = item_price * int(order_item.quantity)
                order_price += item_price
                x += 1

            order.order_price = order_price
            order.save()

            return redirect('orders')
        
        elif 'delete_form' in request.POST:
            Order.objects.filter(pk=order_pk).delete()
            return redirect('orders')
                
    return render(request, 'CLEAR/orders.html', {'orders':order_list, 'customers':customer_objects, 'products':product_objects, 'materials':material_objects, 'product_names': product_names})
'''