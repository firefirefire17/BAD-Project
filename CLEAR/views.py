from django.shortcuts import render, redirect, get_object_or_404
from .models import Textile, Accessory, Product, Product_Accessory, Component, Product_Component, Job_Order, Item, Item_Accessory, Item_Textile, Order_Item, StockIn, StockIn_Accessory, StockIn_Textile, Financial_Value, MaterialKey, Outlet
from django.contrib.auth import authenticate, login, logout
from .forms import RegisterForm, LoginForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.db.models import F, ExpressionWrapper, FloatField, Sum  #used expwrapper for reports - dane
import matplotlib.pyplot as plt
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
import matplotlib.backends.backend_pdf

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

    # assign global values if they exist
    try:
        wage_object = Financial_Value.objects.get(name="labor_wage")
        wage = wage_object.value
    except: # if the global value doesn't exist, assign it to false to flag it for creation later
        wage_object = False

    try:
        vat_object = Financial_Value.objects.get(name="vat")
        vat = vat_object.value
    except:
        vat_object = False


    #create a list of dicts
    for product in product_objects:
        product.updateCost()
        product_data = {
            'product':product,
            'textile_buffers': [],
            'accessories': [],
        }

        unique_textiles = set()
        textile_buffer_list = []
        for product_component in product.product_component_set.all():
            unique_textiles.add(product_component.textile)
        
        for textile in unique_textiles:
            unique_buffers = set()
            for component in textile.product_component_set.filter(product=product):
                unique_buffers.add(component.buffer)
            for buffer in unique_buffers:
                data = {
                    'textile':textile,
                    'buffer': buffer,
                }
                textile_buffer_list.append(data)

        for textile_buffer in textile_buffer_list:
            textile = textile_buffer['textile']
            buffer = textile_buffer['buffer']
            textile_buffer_data = {
                'textile': textile,
                'buffer': buffer,
                'unit': textile.get_unit_display(),
                'components': []
            }

            for component in textile.product_component_set.filter(product=product, buffer=buffer):
                component_data = {
                    'name': component.component.component_name,
                    'height': component.height,
                    'width': component.width,
                    'quantity': component.quantity,
                    'buffer': component.buffer,
                } 
                textile_buffer_data['components'].append(component_data)
            textile_buffer_data['component_count'] = len(textile_buffer_data['components'])
            product_data['textile_buffers'].append(textile_buffer_data)
        for accessory in product.product_accessory_set.all():
            accessory_data = {
                'accessory': accessory.accessory,
                'unit': accessory.accessory.get_unit_display(),
                'quantity': accessory.accessory_quantity,
            }
            product_data['accessories'].append(accessory_data)
        product_data["textile_count"] = len(product_data['textile_buffers'])
        product_data["accessory_count"] = len(product_data['accessories'])
        product_material_list.append(product_data)

    if request.method == "POST":
        print(request.POST)
        action = request.POST.get("action")
        if action == "add_form": # adding products

            name = request.POST.get("name")
            prod_margin = request.POST.get("margin")
            labor_time = request.POST.get("labor")
            misc_margin = request.POST.get("misc")
            retail_price = request.POST.get("retail")
            last_update = request.POST.get("last_update")

            new_product = Product.objects.create(name=name, 
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
                        elif not component_name:
                            pass
                        else: 
                            height = component['height']
                            width = component['width']
                            component_quantity = component['quantity']
                            buffer = component['buffer'] or 0

                            existing_component = Component.objects.filter(component_name=component_name).first()

                            if existing_component:
                                product_component = Product_Component.objects.create(product=new_product, textile=textile_object, component=existing_component, height=height, width=width, quantity=component_quantity, buffer=buffer)
                            else:
                                new_component = Component.objects.create(component_name=component_name)
                                product_component = Product_Component.objects.create(product=new_product, textile=textile_object, component=new_component, height=height, width=width, quantity=component_quantity, buffer=buffer)

            
            accessory_data = json.loads(request.POST.get("accessory_data"))
            for accessory in accessory_data:
                accessory_id = accessory['accessory_id']
                quantity = accessory['quantity']

                if accessory_id == "delete":
                    pass
                else:
                    accessory_object = Accessory.objects.get(material_key__material_key=accessory_id)
                    Product_Accessory.objects.create(product=new_product, accessory=accessory_object, accessory_quantity=quantity)
            
            if retail_price:
                new_product.updateCost()
                new_product.retail_price = retail_price
            else:
                print("no retail")
                new_product.retail_price = new_product.updateCost()

            if last_update:
                new_product.last_update = last_update
            else:
                new_product.last_update = timezone.now().date()
            print(new_product.last_update)

            new_product.save()

            response = {}
            response['status'] = True
            response['msg'] = "Form submitted."
            response['url'] = reverse('products')  # URL to direct is str

            # return dict to ajax
            return JsonResponse(response)

        elif action == "edit_form": # updating products
            product_id = request.POST.get("pk")
            product = Product.objects.get(pk=product_id)

            name = request.POST.get("name")
            prod_margin = request.POST.get("margin")
            labor_time = request.POST.get("labor")
            misc_margin = request.POST.get("misc")
            retail_price = request.POST.get("retail")
            last_update = request.POST.get("last_update")


            #update product attributes
            product.name = name
            product.prod_margin = prod_margin
            product.labor_time = labor_time
            product.misc_margin = int(misc_margin)
            product.last_update = last_update

            if float(retail_price) != product.retail_price:
                print("diff retail")
                product.retail_price = retail_price
                product.last_update = timezone.now().date()

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
                            buffer = component['buffer'] or 0

                            existing_component = Component.objects.filter(component_name=component_name).first()

                            if existing_component:
                                Product_Component.objects.create(product=product, textile=textile_object, component=existing_component, height=height, width=width, quantity=component_quantity, buffer=buffer)
                            else:
                                new_component = Component.objects.create(component_name=component_name)
                                Product_Component.objects.create(product=product, textile=textile_object, component=new_component, height=height, width=width, quantity=component_quantity, buffer=buffer)

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

            product.updateCost()
            product.save()

            response = {}
            response['status'] = True
            response['msg'] = "Form submitted."
            response['url'] = reverse('products')

            # return dict to ajax
            return JsonResponse(response)

        elif 'delete_form' in request.POST: # deleting products
            #delete try
            product.pk = request.POST.get("productMaterial_pk")

            try:
                product = Product.objects.get(pk=product.pk)
                product.delete()

            except Product.DoesNotExist:
                #if it does not exist we pass the shit
                pass
            
            return redirect('products')
        
        elif 'global_values' in request.POST:  # editing global values
            wage_update = request.POST.get("labor_wage")
            vat_update = request.POST.get("VAT")

            if wage_object:
                Financial_Value.objects.filter(name="labor_wage").update(value=wage_update)
            else:
                Financial_Value.objects.create(name="labor_wage", value=wage_update)
            
            if vat_object:
                Financial_Value.objects.filter(name="vat").update(value=vat_update)
            else:
                Financial_Value.objects.create(name="vat", value=vat_update)
            
            return redirect('products')

            
    if not vat_object or not wage_object:
        return render(request, 'CLEAR/products.html', {'products':product_objects, 
                                                   'product_material_list':product_material_list,
                                                   'accessories':accessory_objects,
                                                   'textiles':textile_objects,
                                                   })
    else:
        return render(request, 'CLEAR/products.html', {'products':product_objects, 
                                                   'product_material_list':product_material_list,
                                                   'accessories':accessory_objects,
                                                   'textiles':textile_objects,
                                                   'VAT':vat,
                                                   'wage': wage,
                                                   })

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

        if accessory.stock > 1:
            if unit == 'inch':
                unit = unit + "es"
            else:
                unit = unit + "s"

        material_objects.append({'type': 'accessory', 'material': accessory, 'unit': unit})

    if(request.method=="POST"):
        material_key = request.POST.get("material_key")
        type = request.POST.get("type")

        print(request.POST)

        if "add_form" in request.POST:
            name = request.POST.get("name")
            stock = request.POST.get("stock")
            cost = float(request.POST.get("cost"))
            unit = request.POST.get("unit")

            try:
                stock = int(stock)
            except:
                stock = float(stock)

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
                print("pass")
                Textile.objects.create(name=name, stock=stock, cost=cost, material_key=material_key, unit=unit)
            if type == "accessory":
                print("pass")
                Accessory.objects.create(name=name, stock=stock, cost=cost, material_key=material_key, unit=unit)
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
        
        #if searchitem in request.GET:
           # searchitem = request.GET['searchitem']
           # data = Textile.objects.filter(name__unaccent__icontains=searchitem)


    return render(request, 'CLEAR/materials.html', {'materials':material_objects})

@login_required(login_url="/login")
def job_orders(request):
    product_objects = Product.objects.all()
    textile_objects = Textile.objects.all()
    accessory_objects = Accessory.objects.all()
    outlet_objects = Outlet.objects.all()
    outlet_count = len(outlet_objects)
    order_list = []

    for order in Job_Order.objects.all():
        order_data = {
            'order': order,
            'file_date': order.file_date,
            'completion_date': order.completion_date,
            'status': order.order_status,
            'customer': order.customer,
            'outlet': order.outlet,
            'items': [],
        }
        for order_item in order.order_item_set.all():
            item_data = {
                'item': order_item.item,
                'quantity': order_item.quantity,
                'materials': [],
            }
            for item_textile in order_item.item.item_textile_set.all():
                material_data = {
                    'type': 'textile',
                    'material': item_textile.textile,
                    'bespoke_rate': item_textile.bespoke_rate,
                    'quantity': item_textile.quantity,
                }
                item_data['materials'].append(material_data)
            for item_accessory in order_item.item.item_accessory_set.all():
                material_data = {
                    'type': 'accessory',
                    'material': item_accessory.accessory,
                    'bespoke_rate': item_accessory.bespoke_rate,
                    'quantity': item_accessory.quantity,
                }
                item_data['materials'].append(material_data)
            if item_data['materials']:
                item_data['bespoke'] = 'yes'
            else:
                item_data['bespoke'] = 'no'
            item_data['item_count'] = len(item_data['materials'])
            order_data['items'].append(item_data)
        order_data['item_count'] = len(order_data['items'])
        order_list.append(order_data)
    
    if (request.method == "POST"):
        action = request.POST.get("action")
        print(request.POST)

        file_date = request.POST.get("file_date") 
        status = request.POST.get("status")
        completion_date = request.POST.get("completion_date")
        start_date = request.POST.get("start_date")
        outlet = request.POST.get("outlet")
        customer = request.POST.get("customer")

        print(file_date)

        if action == 'add_form':
            outlet_object = Outlet.objects.get(pk=outlet)
            new_order = Job_Order.objects.create(file_date=file_date, order_status=status, customer=customer, outlet=outlet_object)
            if start_date:
                new_order.start_date = start_date
                new_order.save()
            if completion_date:
                new_order.completion_date = completion_date
                new_order.save()

            item_data = json.loads(request.POST.get("items"))
            for item in item_data:
                product_id = item['order_item']
                if product_id == 'delete':
                    pass
                else:
                    product = Product.objects.get(pk = item['order_item'])
                    quantity = item['quantity']
                    if item['materials']:
                        type = "bespoke"
                    else:
                        type = "regular"

                    new_item = Item.objects.create(product=product, type=type)

                    for material in item['materials']:
                        material_type = material['material_type']
                        item_material = material['item_material']
                        bespoke_rate = material['bespoke_rate']
                        quantity = material['quantity']
                        print(quantity)
                        if item_material == "delete":
                            pass
                        else:
                            if material_type == 'textile':
                                textile_object = Textile.objects.get(material_key__material_key = item_material)
                                Item_Textile.objects.create(item=new_item, textile=textile_object, bespoke_rate=bespoke_rate, quantity=quantity)
                            else:
                                accessory_object = Accessory.objects.get(material_key__material_key = item_material)
                                Item_Accessory.objects.create(item=new_item, accessory=accessory_object, bespoke_rate=bespoke_rate, quantity=quantity)
                    
                    existing_item = new_item.is_duplicate()
                    print(existing_item)
                    if not existing_item:
                        print('pass')
                        Order_Item.objects.create(order=new_order, item=new_item, quantity=quantity)
                    else:
                        new_item.delete()
                        Order_Item.objects.create(order=new_order, item=existing_item, quantity=quantity)
        
            response = {}
            response['status'] = True
            response['msg'] = "Form submitted."
            response['url'] = reverse('orders')

            # return dict to ajax
            return JsonResponse(response)
        elif action == "edit_form":
            outlet_object = Outlet.objects.get(pk=outlet)

            pk = request.POST.get("pk")
            order = Job_Order.objects.get(pk=pk)

            if start_date:
                order.start_date = start_date
            if completion_date:
                order.completion_date = completion_date

            original_status = order.order_status
            if original_status == "completed":
                if status != "completed":
                    order.rollback_stocks(order.get_stocks())
            else:
                if status == "completed":
                    order.deduct_stocks(order.get_stocks())
            
            order.file_date=file_date
            order.order_status=status
            order.customer=customer
            order.outlet=outlet_object

            order.save()

            Order_Item.objects.filter(order=order).delete()
            
            item_data = json.loads(request.POST.get("items"))
            for item in item_data:
                product_id = item['order_item']
                if product_id == 'delete':
                    pass
                else:
                    product = Product.objects.get(pk = item['order_item'])
                    quantity = item['quantity']
                    if item['materials']:
                        type = "bespoke"
                    else:
                        type = "regular"

                    new_item = Item.objects.create(product=product, type=type)

                    for material in item['materials']:
                        material_type = material['material_type']
                        item_material = material['item_material']
                        bespoke_rate = material['bespoke_rate']
                        quantity = material['quantity']
                        print(material_type)
                        print(item_material)
                        print(quantity)
                        if item_material == "delete":
                            pass
                        else:
                            if material_type == 'textile':
                                print('textile')
                                textile_object = Textile.objects.get(material_key__material_key = item_material)
                                Item_Textile.objects.create(item=new_item, textile=textile_object, bespoke_rate=bespoke_rate, quantity=quantity)
                            else:
                                print('accessory')
                                accessory_object = Accessory.objects.get(material_key__material_key = item_material)
                                Item_Accessory.objects.create(item=new_item, accessory=accessory_object, bespoke_rate=bespoke_rate, quantity=quantity)
                    
                    existing_item = new_item.is_duplicate()
                    print(existing_item)
                    if not existing_item:
                        print('pass')
                        Order_Item.objects.create(order=order, item=new_item, quantity=quantity)
                    else:
                        new_item.delete()
                        Order_Item.objects.create(order=order, item=existing_item, quantity=quantity)
            order.save() 
            response = {}
            response['status'] = True
            response['msg'] = "Form submitted."
            response['url'] = reverse('orders')

            # return dict to ajax
            return JsonResponse(response)
        elif 'delete_form' in request.POST:
            pk = request.POST.get("pk")
            Job_Order.objects.filter(pk=pk).delete()
            return redirect('orders')
        elif action == 'outlets':
            print(request.POST)
            outlet_data = json.loads(request.POST.get("outlets"))
            print(outlet_data)

            for outlet in outlet_data:
                outlet_id = outlet['outlet_id']
                outlet_name = outlet['outlet_name']
                print(outlet_id)
                if outlet_id:
                    outlet_object = Outlet.objects.get(pk=outlet_id)
                    print(outlet_id)
                    if outlet_name == 'delete':
                        outlet_object.delete()
                        outlet_object.save()
                    else:
                        outlet_object.outlet_name = outlet_name
                        outlet_object.save()
                else:
                    print('pass')
                    Outlet.objects.create(outlet_name=outlet_name)
            response = {}
            response['status'] = True
            response['msg'] = "Form submitted."
            response['url'] = reverse('orders')

            # return dict to ajax
            return JsonResponse(response)



    return render(request, 'CLEAR/job_orders.html', {'orders':order_list, 'products':product_objects, 'accessories':accessory_objects, 'textiles':textile_objects, 'outlets':outlet_objects, 'outlet_count':outlet_count})


@login_required(login_url="/login")
def reports(request):
    if request.method == "POST":
        reptype = request.POST.get("reptype")
        if reptype == 'materials':
            return redirect('material_report') 
        elif reptype == 'production':
            return redirect('production_reports')  
        elif reptype == 'pricing':
            return redirect('pricing_reports')
        elif reptype == 'shopping_list':
            return redirect('shopping_list_reports')  
    return render(request, 'CLEAR/reports.html')


#-------ATTEMPT ON MATERIAL REPORTS (NEEDS WORK BUT DISPLAYS)--------#
'''
@login_required(login_url="/login")
def material_report(request):
    textile_objects = Textile.objects.annotate(total_cost=ExpressionWrapper(F('stock') * F('cost'), output_field=FloatField()))
    accessory_objects = Accessory.objects.annotate(total_cost=ExpressionWrapper(F('stock') * F('cost'), output_field=FloatField()))

    material_data = []

    for textile in textile_objects:
        unit = textile.get_unit_display().removeprefix("per ")
        material_data.append({'type': 'textile', 'pk': textile.pk, 'name': textile.name, 'unit': unit, 'stock': textile.stock, 'cost': textile.cost, 'total_cost': textile.total_cost})

    for accessory in accessory_objects:
        unit = accessory.get_unit_display().removeprefix("per ")
        material_data.append({'type': 'accessory', 'pk': accessory.pk, 'name': accessory.name, 'unit': unit, 'stock': accessory.stock, 'cost': accessory.cost, 'total_cost': accessory.total_cost})

    material_data = sorted(material_data, key=lambda x: x['total_cost'], reverse=True)
    
    total_stock = sum(item['stock'] for item in material_data)
    total_cost = sum(item['total_cost'] for item in material_data)

    context = {
        'materials': material_data,
        'total_stock': total_stock,
        'total_cost': total_cost,
    }

    datenow = timezone.now().date()
    return render(request, 'CLEAR/material_report.html', {'materials':material_data, 'today': datenow,})
'''

@login_required(login_url="/login")
def material_report(request):
    textile_objects = Textile.objects.all()
    accessory_objects = Accessory.objects.all()
    material_data = []

    
    for textile in textile_objects:
        unit = textile.get_unit_display()
        unit = unit.removeprefix("per ")

        material_data.append({'type': 'textile', 'pk': textile, 'unit': unit})

    for accessory in accessory_objects:
        unit = accessory.get_unit_display()
        unit = unit.removeprefix("per ")

        if accessory.stock > 1:
            if unit == 'inch':
                unit = unit + "es"
            else:
                unit = unit + "s"

        material_objects.append({'type': 'accessory', 'material': accessory, 'unit': unit})

    # Create a dictionary to hold the data for each column
    data_dict = {
        "Material Key": [item["pk"] for item in material_data],
        "Name": [item["name"] for item in material_data],
        "Type": [item["type"].title() for item in material_data],  # Title-case the type
        "Stock": [f"{item['stock']:.2f} {item['unit']}" for item in material_data],  # Format stock and unit
        "Cost": [item["cost"] for item in material_data]
    }

    material_objects = sorted(material_objects, key=lambda x: x['material'].stock)
    datenow = timezone.now().date()

    return render(request, 'CLEAR/material_report.html', {'materials':material_objects, 'today': datenow,})

@login_required(login_url="/login")
def production_report(request):
    return render(request, 'CLEAR/production_report.html')

@login_required(login_url="/login")
def pricing_report(request):
    return render(request, 'CLEAR/pricing_report.html')

@login_required(login_url="/login")
def shopping_list(request):
    return render(request, 'CLEAR/shopping_list.html')


@login_required(login_url="/login")
def stock_in(request):
    textile_objects = Textile.objects.all()
    accessory_objects = Accessory.objects.all()
    stockIn_objects = StockIn.objects.all()

    stockIn_material_list = []
    for stock_in in stockIn_objects:
        stock_data = {
            'stock_in': stock_in,
            'materials': [],
        }
        for stockIn_textile in stock_in.stockin_textile_set.all():
            data = {
                'textile': stockIn_textile.textile,
                'quantity': stockIn_textile.quantity,
                'cost': stockIn_textile.cost,
                'type': 'textile',
                'pk': stockIn_textile.textile.material_key.material_key,

            }
            stock_data['materials'].append(data)
        for stockIn_accessory in stock_in.stockin_accessory_set.all():
            data = {
                'accessory': stockIn_accessory.accessory,
                'quantity': stockIn_accessory.quantity,
                'cost': stockIn_accessory.cost,
                'type': 'accessory',
                'pk': stockIn_accessory.accessory.material_key.material_key,
            }
            stock_data['materials'].append(data)
        stock_data['material_count'] = len(stock_data['materials'])
        stockIn_material_list.append(stock_data)

    if(request.method=="POST"):
        action = request.POST.get("action")
        print(request.POST)
        if action == "add_form":
            date = request.POST.get("date")

            new_stockIn = StockIn.objects.create(transaction_date=date)
            material_data = json.loads(request.POST.get("materials"))

            for material in material_data:
                material_id = material['stock_material']
                material_type = material['material_type']
                quantity = material['quantity']
                cost = material['cost']

                if material_id == "delete":
                    pass
                else: 
                    if material_type == "textile":
                        material_object = Textile.objects.get(material_key__material_key = material_id)
                        StockIn_Textile.objects.create(textile=material_object, stock_in=new_stockIn, quantity=quantity, cost=cost)
                        material_object.stock += float(quantity)
                    else:
                        material_object = Accessory.objects.get(material_key__material_key = material_id)
                        StockIn_Accessory.objects.create(accessory=material_object, stock_in=new_stockIn, quantity=quantity, cost=cost)   
                        material_object.stock += int(quantity)
                    material_object.save()

            new_stockIn.updateCost()
            new_stockIn.save()

            response = {}
            response['status'] = True
            response['msg'] = "Form submitted."
            response['url'] = reverse('stock_in')

            # return dict to ajax
            return JsonResponse(response)
        
        elif action == 'edit_form':
            date = request.POST.get("date")
            pk = request.POST.get("pk")

            stockIn_object = StockIn.objects.get(pk=pk)
            material_data = json.loads(request.POST.get("materials"))

            stockIn_object.transaction_date = date

            acc_to_delete = StockIn_Accessory.objects.filter(stock_in=stockIn_object)
            textile_to_delete = StockIn_Textile.objects.filter(stock_in=stockIn_object)

            for stock_material in textile_to_delete:
                stock_material.textile.stock -= stock_material.quantity
                stock_material.textile.save()
                stock_material.delete()
            for stock_material in acc_to_delete:
                stock_material.accessory.stock -= stock_material.quantity
                stock_material.accessory.save()
                stock_material.delete()


            for material in material_data:  
                print("pass")
                material_id = material['stock_material']
                material_type = material['material_type']
                quantity = material['quantity']
                cost = material['cost']

                if material_id == "delete":
                    pass
                else: 
                    if material_type == "textile":
                        quantity = float(quantity)
                        material_object = Textile.objects.get(material_key__material_key = material_id)
                        StockIn_Textile.objects.create(textile=material_object, stock_in=stockIn_object, quantity=quantity, cost=cost)
                        material_object.stock += quantity
                    else:
                        print('accessory')
                        material_object = Accessory.objects.get(material_key__material_key = material_id)
                        StockIn_Accessory.objects.create(accessory=material_object, stock_in=stockIn_object, quantity=quantity, cost=cost)   
                        material_object.stock += int(quantity)
                    material_object.save()
            stockIn_object.updateCost()
            stockIn_object.save()

            response = {}
            response['status'] = True
            response['msg'] = "Form submitted."
            response['url'] = reverse('stock_in')
            print(reverse('stock_in'))

            # return dict to ajax
            return JsonResponse(response)
        elif 'delete_form' in request.POST:
            pk = request.POST.get("pk")
            StockIn.objects.filter(pk=pk).delete()
            return redirect('stock_in')



    return render(request, 'CLEAR/stock_in.html', {'textiles':textile_objects, 'accessories': accessory_objects, 'stock_ins':stockIn_material_list})

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

def get_material_options(request): # function used to change materials in stock-in upon material type change 
    material_type = request.GET.get('material_type') 
 
    materials = [] 
    if material_type == "textile": 
        materials = Textile.objects.all() 
    else: 
        materials = Accessory.objects.all() 
 
    options = {} 
    for material in materials: 
        pk = material.material_key.material_key 
        name = material.name 
        options[pk] = name 
 
    return JsonResponse({'options': options}) 

def generate_material_pd(request):
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

        if accessory.stock > 1:
            if unit == 'inch':
                unit = unit + "es"
            else:
                unit = unit + "s"

        material_objects.append({'type': 'accessory', 'material': accessory, 'unit': unit})
    pdf_bytes = pandas_df_to_table(dataframe)

    # Serve PDF file as response
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="output.pdf"'
    return response
 
# this is a function used in products to get the cost of each product component 
def get_prodComponentCost(height, width, quantity, textile_unit, textile_cost): 
    sq_inch  = float(height)*float(width) 
 
    if textile_unit == "FT": 
        final_unit = sq_inch / 144 
    elif textile_unit == "M": 
        final_unit = sq_inch / 1550.0031 
    else: 
        final_unit = sq_inch 
     
    final_quantity = final_unit*float(quantity) 
    final_cost = final_quantity*float(textile_cost) 
    return final_cost 

def pandas_df_to_table(dataframe):
    # Convert DataFrame to matplotlib table
    fig, ax = plt.subplots(figsize=(7, 3))  # Adjust size as needed
    ax.axis('tight')
    ax.axis('off')
    table = ax.table(cellText=dataframe.values, colLabels=dataframe.columns, loc='center')

    # Convert matplotlib table to PDF table
    pdf_bytes = BytesIO()
    pdf = matplotlib.backends.backend_pdf.PdfPages(pdf_bytes)
    pdf.savefig(fig, bbox_inches='tight')
    pdf.close()

    return pdf_bytes.getvalue()

def save_pdf(pdf_bytes, output_filename):
    # Write PDF bytes to a file
    with open(output_filename, 'wb') as f:
        f.write(pdf_bytes)

