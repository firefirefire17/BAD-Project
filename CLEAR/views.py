from django.shortcuts import render, redirect, get_object_or_404
from .models import Textile, Accessory, Product, Product_Accessory, Component, Product_Component, Job_Order, Item, Item_Accessory, Item_Textile, Order_Item, Transaction, Transaction_Accessory, Transaction_Textile, Global_Value, Account, MaterialKey
from django.contrib.auth import authenticate, login, logout
from .forms import RegisterForm, LoginForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse

import json



# Create your views here.

@login_required(login_url="/login") # this is to restrict access if not logged in
def dashboard(request):
    return render(request, 'CLEAR/dashboard.html')


@login_required(login_url="/login")
def products(request):
    product_objects = Product.objects.all()
    accessory_objects = Accessory.objects.all()
    textile_objects = Textile.objects.all()

    product_material_list = []


    #create a list of dicts
    temp_list = []
    for product in product_objects:
        product_data = {
            'product':product,
            'textiles': [],
            'accessories': [],
        }

        unique_textiles = set()
        for product_component in product.product_component_set.all():
            unique_textiles.add(product_component.textile)

        for textile in unique_textiles:
            textile_data = {
                'textile': textile,
                'unit': textile.unit,
                'components': []
            }
            for component in textile.product_component_set.filter(product=product):
                component_data = {
                    'name': component.component.component_name,
                    'height': component.height,
                    'width': component.width,
                    'quantity': component.quantity,
                }
                textile_data['components'].append(component_data)
            textile_data['component_count'] = len(textile_data['components'])
            product_data['textiles'].append(textile_data)
        for accessory in product.product_accessory_set.all():
            accessory_data = {
                'accessory': accessory.accessory,
                'unit': accessory.accessory.unit,
                'quantity': accessory.accessory_quantity,
            }
            product_data['accessories'].append(accessory_data)
        product_data["textile_count"] = len(product_data['textiles'])
        product_data["accessory_count"] = len(product_data['accessories'])
        product_material_list.append(product_data)
    if request.method == "POST":
        print(request.POST)
        action = request.POST.get("action")
        if action == "add_form":
            #adding of stuff

            name = request.POST.get("name")
            prod_margin = request.POST.get("margin")
            stock = request.POST.get("stock")
            labor_time = request.POST.get("labor")
            misc_margin = request.POST.get("misc")

            new_product = Product.objects.create(name=name, 
                                                stock=stock, 
                                               prod_margin=prod_margin, 
                                               labor_time=labor_time, 
                                             misc_margin=misc_margin)

            textile_data = json.loads(request.POST.get("textile_data"))
            for textile in textile_data:
                textile_id = textile['textile_id']

                if textile_id == "delete":
                    pass
                else:
                    textile_object = Textile.objects.get(material_key__material_key = textile_id)
                    
                    for component in textile['components']:
                        component_name = component['component_name'].lower()

                        if component_name == 'delete':
                            pass
                        else: 
                            height = component['height']
                            width = component['width']
                            component_quantity = component['quantity']

                            existing_component = Component.objects.filter(component_name=component_name).first()

                            if existing_component:
                                Product_Component.objects.create(product=new_product, textile=textile_object, component=existing_component, height=height, width=width, quantity=component_quantity)
                            else:
                                new_component = Component.objects.create(component_name=component_name)
                                Product_Component.objects.create(product=new_product, textile=textile_object, component=new_component, height=height, width=width, quantity=component_quantity)

            
            accessory_data = json.loads(request.POST.get("accessory_data"))
            for accessory in accessory_data:
                accessory_id = accessory['accessory_id']
                quantity = accessory['quantity']

                if accessory_id == "delete":
                    pass
                else:
                    accessory_object = Accessory.objects.get(material_key__material_key=accessory_id)
                    Product_Accessory.objects.create(product=new_product, accessory=accessory_object, accessory_quantity=quantity)

            response = {}
            response['status'] = True
            response['msg'] = "Form submitted."
            response['url'] = reverse('products')  # URL to direct is str

            # return dict to ajax
            return JsonResponse(response)

        elif action == "edit_form":
            product_id = request.POST.get("pk")
            product = Product.objects.get(pk=product_id)

            name = request.POST.get("name")
            prod_margin = request.POST.get("margin")
            stock = request.POST.get("stock")
            labor_time = request.POST.get("labor")
            misc_margin = request.POST.get("misc")

            #update product attributes
            product.name = name
            product.stock = stock
            product.prod_margin = prod_margin
            product.labor_time = labor_time
            product.misc_margin = int(misc_margin)

            product.save()

            #update textiles
            Product_Component.objects.filter(product=product).delete()

            textile_data = json.loads(request.POST.get("textile_data"))
            for textile in textile_data:
                textile_id = textile['textile_id']

                if textile_id == "delete":
                    pass
                else:
                    textile_object = Textile.objects.get(material_key__material_key = textile_id)
                    
                    for component in textile['components']:
                        component_name = component['component_name'].lower()

                        if component_name == 'delete':
                            pass
                        else: 
                            height = component['height']
                            width = component['width']
                            component_quantity = component['quantity']

                            existing_component = Component.objects.filter(component_name=component_name).first()

                            if existing_component:
                                Product_Component.objects.create(product=product, textile=textile_object, component=existing_component, height=height, width=width, quantity=component_quantity)
                            else:
                                new_component = Component.objects.create(component_name=component_name)
                                Product_Component.objects.create(product=product, textile=textile_object, component=new_component, height=height, width=width, quantity=component_quantity)

            #update accs
            Product_Accessory.objects.filter(product=product).delete()       
            accessory_data = json.loads(request.POST.get("accessory_data"))
            for accessory in accessory_data:
                accessory_id = accessory['accessory_id']
                quantity = accessory['quantity']

                if accessory_id == "delete":
                    pass
                else:
                    accessory_object = Accessory.objects.get(material_key__material_key=accessory_id)
                    Product_Accessory.objects.create(product=product, accessory=accessory_object, accessory_quantity=quantity)

            response = {}
            response['status'] = True
            response['msg'] = "Form submitted."
            response['url'] = reverse('products')  # URL to products view

            # return dict to ajax
            return JsonResponse(response)

        elif 'delete_form' in request.POST:
            #delete old
            '''
            product.pk = request.POST.get("productMaterial_pk")
            Product.objects.filter(pk=product_pk).delete()
            '''

            #delete try
            product.pk = request.POST.get("productMaterial_pk")

            try:
                product = Product.objects.get(pk=product.pk)
                product.delete()

            except Product.DoesNotExist:
                #if it does not exist we pass the shit
                pass
            
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
        unit = textile.get_unit_display()
        unit = unit.removeprefix("per ")
        material_objects.append({'type': 'textile', 'material': textile, 'unit': unit})

    for accessory in accessory_objects:
        unit = accessory.get_unit_display()
        unit = unit.removeprefix("per ")
        material_objects.append({'type': 'accessory', 'material': accessory, 'unit': unit})

    print(material_objects)

    if(request.method=="POST"):
        material_key = request.POST.get("material_key")
        type = request.POST.get("type")

        if "add_form" in request.POST:
            name = request.POST.get("name")
            stock = float(request.POST.get("stock"))
            cost = float(request.POST.get("cost"))

            if len(name) > 50:
                error_message = "Input cannot be more than 50 characters"
                return render(request, 'CLEAR/materials.html', {'materials': material_objects, 'error_message': error_message})
            
            if stock < 0 or stock > 999:
                #backend message
                error_message = "Input cannot be negative or more than 999"
                return render(request, 'CLEAR/materials.html', {'materials': material_objects, 'error_message': error_message})
            
            if type == "accessory":
                if isinstance(stock, float):
                    error_message = "Stock input cannot be a decimal number"
                    return render(request, 'CLEAR/materials.html', {'materials': material_objects, 'error_message': error_message})
                    
            if cost < 0:
                #backend message
                error_message = "Input cannot be negative"
                return render(request, 'CLEAR/materials.html', {'materials': material_objects, 'error_message': error_message})

            material_key = MaterialKey.objects.create()
            print(material_key)

            if type == "textile": 
                Textile.objects.create(name=name, stock=stock, cost=cost, material_key=material_key)
            if type == "accessory":
                Accessory.objects.create(name=name, stock=stock, cost=cost, material_key=material_key)
            return redirect('materials')

        elif "edit_form" in request.POST:
            name = request.POST.get("name")
            stock = request.POST.get("stock")
            cost = float(request.POST.get("cost"))

            if len(name) > 50:
                error_message = "Input cannot be more than 50 characters"
                return render(request, 'CLEAR/materials.html', {'materials': material_objects, 'error_message': error_message})
          
            if type == "accessory":
                if isinstance(stock, float):
                    error_message = "Stock input cannot be a decimal number"
                    return render(request, 'CLEAR/materials.html', {'materials': material_objects, 'error_message': error_message})
            
            if cost < 0:
                #backend message
                error_message = "Input cannot be negative"
                return render(request, 'CLEAR/materials.html', {'materials': material_objects, 'error_message': error_message})

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
