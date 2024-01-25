from django.shortcuts import render, redirect, get_object_or_404
from .models import Material, Product, Product_Material, Order, Customer, Item, Item_Material, Order_Item
from django.db import transaction

# Create your views here.
def login(request):
    return render(request, 'CLEAR/base.html')

def dashboard(request):
    return render(request, 'CLEAR/dashboard.html')

def products(request):
    product_objects = Product.objects.all()
    material_objects = Material.objects.all()
    product_material_list = []

    # create a list of dictionaries, each dictionary pertaining to one product and its associated information
    for product in product_objects:
        data = {
            'product': product,
            'materials': product.product_material_set.all(),
            'product_materials_count': product.product_material_set.count()
        }
        product_material_list.append(data)
    
    if(request.method=="POST"):
        stock = request.POST.get("stock")
        name = request.POST.get("name")

        print(request.POST)

        
        if 'edit_form' in request.POST:
            product_pk = request.POST.get("product_pk")
            product = get_object_or_404(Product, pk=product_pk)

            x = 1
            while True:
                pm_pk = request.POST.get(f"{product_pk}_productMaterial_pk{x}")
                quantity = request.POST.get(f"quantity{x}")
                materialID = request.POST.get(f"{product_pk}_product_material{x}")

                if materialID is None:
                    break
                else:
                    if pm_pk: 
                        if materialID == "delete":
                            Product_Material.objects.filter(pk=pm_pk).delete()
                        else:
                            Product_Material.objects.filter(pk=pm_pk).update(material=materialID, quantity=quantity)
                    else:
                        if materialID != "delete":
                            material_object = get_object_or_404(Material, pk=materialID)
                            Product_Material.objects.create(product=product, material=material_object, quantity=quantity)
                x+=1
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
            product_cost = 0
            while True:
                quantity = request.POST.get(f"quantity{x}")
                materialID = request.POST.get(f"product_material{x}")
                print(f"{materialID}")

                if materialID is None:
                    break
                else:
                    if materialID == "delete":
                        pass
                    else:
                        material = get_object_or_404(Material, pk=materialID)
                        product_material = Product_Material.objects.create(product=new_product, material=material, quantity=quantity)

                        # add the cost of each material to the product price
                        product_cost += material.cost*material.markup*int(product_material.quantity)
                x += 1
            new_product.cost = product_cost
            new_product.save()
            return redirect('products')

    return render(request, 'CLEAR/products.html', {'products':product_objects, 'product_materials_list':product_material_list, 'materials':material_objects})

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

            ''' 
            if customer_pk == "new_customer":
                existing_customer = Customer.objects.filter(name=customer_name).first()
                if existing_customer:
                    # customer already exists error
                    pass
                else:
                    order_customer = Customer.objects.create(name=customer_name, mobile_number=customer_number)
            else:
                order_customer = Customer.objects.filter(pk=customer_pk).first()
            '''

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
            '''
            current_customer_pk = request.POST.get("current_customer_pk")
            if current_customer_pk == customer_pk:
                Customer.objects.filter(pk=customer_pk).update(name=customer_name, mobile_number=customer_number)
            '''

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



def materials(request):
    material_objects = Material.objects.all()
    last = Material.objects.last()

    if(request.method=="POST"):
        name = request.POST.get("name")
        stock = request.POST.get("stock")
        cost = request.POST.get("cost")
        type = request.POST.get("type")
        if type == "leather":
            unit = "per foot"
        elif type == "lining":
            unit = "per inch"
        else:
            unit = "per piece"

        if "add_form" in request.POST:
            markup = float(request.POST.get("markup"))
            total_value = float(stock)*float(cost) 
            Material.objects.create(name=name, stock=stock, cost=cost, type=type, markup=markup, unit=unit, total_value=total_value)
            return redirect('materials')

        elif "edit_form" in request.POST:
            markup = float(request.POST.get("markup"))
            total_value = float(stock)*float(cost)
            pk=request.POST.get("pk")
            Material.objects.filter(pk=pk).update(name=name, stock=stock, cost=cost, type=type, markup=markup, unit=unit, total_value=total_value)
            return redirect('materials')

        elif "delete_form" in request.POST:
            pk=request.POST.get("pk")
            Material.objects.filter(pk=pk).delete()
            return redirect('materials')


    return render(request, 'CLEAR/materials.html', {'materials':material_objects})

def reports(request):
    return render(request, 'CLEAR/reports.html')

