from django.shortcuts import render, redirect, get_object_or_404
from .models import Textile, Accessory, Product, Product_Accessory, Component, Product_Component, Job_Order, Item, Item_Accessory, Item_Textile, Order_Item, StockIn, StockIn_Accessory, StockIn_Textile, Financial_Value, MaterialKey, Outlet, Account
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import RegisterForm, LoginForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, FileResponse
from django.urls import reverse
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from django.db.models.functions import Cast
from .decorators import owner_required
from django.contrib.auth.models import User

from datetime import datetime, timedelta
import pandas as pd
import io
from django.db.models import F, ExpressionWrapper, FloatField, Sum  #used expwrapper for reports - dane
import matplotlib.pyplot as plt
from io import BytesIO
import matplotlib.backends.backend_pdf
from django.template.defaultfilters import date as django_date

import json

def chart_data(request):

    current_date = timezone.now().date()
    start_date = current_date - timedelta(days=30)
    end_date = current_date + timedelta(days=30)

    outlet_objects = Outlet.objects.all()
    outlet_data = []
    for outlet in outlet_objects:
        job_order_count = outlet.job_order_set.filter(file_date__range=[start_date, end_date]).count()
        outlet_data.append({"y": job_order_count, "label": outlet.outlet_name})

    return JsonResponse(outlet_data, safe=False)

# Create your views here.
@login_required(login_url="/login") # this is to restrict access if not logged in
def dashboard(request): 

    product_objects = Product.objects.all().exclude(name="test_product_test_product_test")
    # Get the current date
    order_objects = Job_Order.objects.all()

    textile_objects = Textile.objects.all()
    accessory_objects = Accessory.objects.all()
    outlet_objects = Outlet.objects.all()
    outlet_count = len(outlet_objects)

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

    material_objects = [material for material in material_objects if int(material['material'].stock) == 0]

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
    
    return render(request, 'CLEAR/dashboard.html', {'wage' : wage, 'vat': vat, 'orders':order_objects, 'products':product_objects, 'accessories':accessory_objects, 'textiles':textile_objects, 'outlets':outlet_objects, 'outlet_count':outlet_count, 'materials': material_objects})
    

# search and filter product
@login_required(login_url="/login")
def search_products(request):
    product_objects = Product.objects.all()

    if request.method == "GET":
        search_query = request.GET.get('q')

        if search_query:
            product_objects = [product for product in product_objects if search_query.lower() in product.name.lower()]
        table_data = []
        for product in product_objects:
            if product.name == "test_product_test_product_test":
                continue
            table_data.append({
              'product_pk' : product.pk,
              'product_name' : product.name.title(),
              'product_retailprice' : product.retail_price,
              'product_lastupdate' : product.last_update
            })

    return JsonResponse({'table_data' : table_data})


@login_required(login_url="/login")
def products(request):
    product_objects = Product.objects.all()
    accessory_objects = Accessory.objects.all()
    textile_objects = Textile.objects.all()
    order_objects = Job_Order.objects.all()



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
        if product.name == "test_product_test_product_test":
            continue
        product.updateCost('update')
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
            response = {}
            response['status'] = True
            try:
                with transaction.atomic():
                    name = request.POST.get("name").lower()
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
                                    response['error'] = "Please input a valid component name"
                                    response['status'] = False
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
                        print('pass')
                        print('retail')
                        new_product.updateCost('update')
                        new_product.retail_price = retail_price
                    else:
                        print("no retail")
                        new_product.retail_price = new_product.updateCost('update')

                    if last_update:
                        new_product.last_update = last_update
                    else:
                        new_product.last_update = timezone.now().date()
                    print(new_product.last_update)

                    new_product.save()

                    if response['status'] == False:
                        raise Exception("An error has occured during the transaction")
            except:
                pass
            # return dict to ajax
            response['url'] = reverse('products')  # URL to direct is str
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
                        elif not component_name:
                            error_message = "Please input component name"
                            return render(request, 'CLEAR/products.html', {'products':product_objects, 
                                                   'product_material_list':product_material_list,
                                                   'accessories':accessory_objects,
                                                   'textiles':textile_objects,
                                                   'VAT':vat,
                                                   'wage': wage,
                                                   })
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

            product.updateCost('update')
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
                                                   'job_orders': order_objects
                                                   })
    else:
        return render(request, 'CLEAR/products.html', {'products':product_objects, 
                                                   'product_material_list':product_material_list,
                                                   'accessories':accessory_objects,
                                                   'textiles':textile_objects,
                                                   'VAT':vat,
                                                   'wage': wage,
                                                   'job_orders': order_objects
                                                   })

# search and filter functionality
@login_required(login_url="/login")
def filter_materials(request):
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
    
    if request.method == "GET":
        search_query = request.GET.get('q')
        filterstock = request.GET.get('filterstock')

        if search_query:
            material_objects = [material for material in material_objects if search_query.lower() in material['material'].name.lower()]
        if filterstock == 'out_of_stock':
            material_objects = [material for material in material_objects if int(material['material'].stock) == 0]
        elif filterstock == 'in_stock':
            material_objects = [material for material in material_objects if int(material['material'].stock) > 0]
        

    # json constructor
        table_data = []
        for material in material_objects:
            stock = f"{material['material'].stock} {material['unit']}"
            cost = f"PHP {material['material'].cost:.2f}"
            table_data.append({
                'type': material['type'],
                'material_id': material['material'].material_key.material_key,
                'material_name': material['material'].name.title(),
                'stock': stock,
                'cost': cost,
                'unit': material['unit'],
            })


    return JsonResponse({'table_data': table_data})


@login_required(login_url="/login")
def materials(request):
    order_objects = Job_Order.objects.all()

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
            name = request.POST.get("name").lower()
            stock = request.POST.get("stock")
            cost = float(request.POST.get("cost"))
            unit = request.POST.get("unit")

            if not stock:
                error_message = "Please input a valid stock number"
                return render(request, 'CLEAR/materials.html', {'materials': material_objects, 'error_message': error_message,})
            
            if not cost:
                error_message = "Please input a valid cost"
                return render(request, 'CLEAR/materials.html', {'materials': material_objects, 'error_message': error_message,})

            try:
                stock = int(stock)
            except:
                stock = float(stock)

            if len(name) > 50:
                error_message = "Input cannot be more than 50 characters"
                return render(request, 'CLEAR/materials.html', {'materials': material_objects, 'error_message': error_message,})
            
            if stock < 0 or stock > 999:
                #backend message
                error_message = "Input cannot be negative or more than 999"
                return render(request, 'CLEAR/materials.html', {'materials': material_objects, 'error_message': error_message,})
            
            if type == "accessory":
                if isinstance(stock, float):
                    error_message = "Stock input cannot be a decimal number"
                    return render(request, 'CLEAR/materials.html', {'materials': material_objects, 'error_message': error_message,})
                    
            if cost < 0:
                #backend message
                error_message = "Input cannot be negative"
                return render(request, 'CLEAR/materials.html', {'materials': material_objects, 'error_message': error_message,})
            
            if not name:
                error_message = "Please input a material name"
                return render(request, 'CLEAR/materials.html', {'materials': material_objects, 'error_message': error_message,})
            

            
            material_key = MaterialKey.objects.create()
            print(material_key)


            if type == "textile": 
                existing_material = Textile.objects.filter(name=name)
                if existing_material:
                    error_message = "Material already exists"
                    return render(request, 'CLEAR/materials.html', {'materials': material_objects, 'error_message': error_message,})
                else:
                    print("pass")
                    Textile.objects.create(name=name, stock=stock, cost=cost, material_key=material_key, unit=unit)
            if type == "accessory":
                existing_material = Accessory.objects.filter(name=name)                
                if existing_material:
                    error_message = "Material already exists"
                    return render(request, 'CLEAR/materials.html', {'materials': material_objects, 'error_message': error_message,})
                else:
                    print("pass")
                    Accessory.objects.create(name=name, stock=stock, cost=cost, material_key=material_key, unit=unit)
            return redirect('materials')

        elif "edit_form" in request.POST:
            name = request.POST.get("name")
            stock = request.POST.get("stock")
            cost = float(request.POST.get("cost"))

            if not stock:
                error_message = "Please input a valid stock number"
                return render(request, 'CLEAR/materials.html', {'materials': material_objects, 'error_message': error_message,})
            
            if not cost:
                error_message = "Please input a valid cost"
                return render(request, 'CLEAR/materials.html', {'materials': material_objects, 'error_message': error_message,})

            if len(name) > 50:
                error_message = "Input cannot be more than 50 characters"
                return render(request, 'CLEAR/materials.html', {'materials': material_objects, 'error_message': error_message,})
        
            if type == "accessory":
                if isinstance(stock, float):
                    error_message = "Stock input cannot be a decimal number"
                    return render(request, 'CLEAR/materials.html', {'materials': material_objects, 'error_message': error_message,})
            
            if cost < 0:
                #backend message
                error_message = "Input cannot be negative"
                return render(request, 'CLEAR/materials.html', {'materials': material_objects, 'error_message': error_message,})

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

    return render(request, 'CLEAR/materials.html', {'materials':material_objects, 'job_orders': order_objects})

@login_required(login_url="/login")
def search_joborders(request):
    joborder_objects = Job_Order.objects.all()

    if request.method == "GET":
        search_query = request.GET.get('q')
        selected_statuses = request.GET.getlist('status[]')  # Get list of selected statuses
        if search_query:
            joborder_objects = [joborder for joborder in joborder_objects if
                                 search_query.lower() in joborder.customer.lower() or
                                 search_query.lower() in joborder.outlet.outlet_name.lower()]
        if selected_statuses:
            joborder_objects = [joborder for joborder in joborder_objects if joborder.order_status in selected_statuses]
            
        table_data = []
        for joborder in joborder_objects:
            table_data.append({
                'joborder_pk': joborder.pk,
                'joborder_customername': joborder.customer,
                'joborder_outletname': joborder.outlet.outlet_name,
                'joborder_filedate': django_date(joborder.file_date, "F j, Y"),
                'joborder_status': joborder.order_status.title(),
                'joborder_completiondate': django_date(joborder.completion_date, "F j, Y"),
            })

    return JsonResponse({'table_data': table_data})

    

@login_required(login_url="/login")
def job_orders(request):
    order_objects = Job_Order.objects.all()

    product_objects = Product.objects.all().exclude(name="test_product_test_product_test")
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
            print(order_item.item.cost)
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

        if action == 'add_form':
            response = {}
            response['status'] = True

            with transaction.atomic():
                outlet_object = Outlet.objects.get(pk=outlet)
                new_order = Job_Order.objects.create(file_date=file_date, order_status=status, customer=customer, outlet=outlet_object)
                if start_date:
                    new_order.start_date = start_date
                    new_order.save()
                if completion_date:
                    new_order.completion_date = completion_date
                    new_order.save()
                    print('completion-date')
                    print(new_order.completion_date)

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

                        bespoke_cost = 0
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
                                bespoke_cost += float(bespoke_rate)
                        
                        new_item.cost = new_item.product.retail_price + bespoke_cost
                        new_item.save()

                        existing_item = new_item.is_duplicate()
                        print(existing_item)

                        quantity = item['quantity']
                        if not existing_item:
                            print('pass')
                            Order_Item.objects.create(order=new_order, item=new_item, quantity=quantity)
                        else:
                            new_item.delete()
                            Order_Item.objects.create(order=new_order, item=existing_item, quantity=quantity)

            if status == "completed":
                new_order.deduct_stocks(new_order.get_stocks())
        
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

                    bespoke_cost = 0
                    for material in item['materials']:
                        material_type = material['material_type']
                        item_material = material['item_material']
                        bespoke_rate = material['bespoke_rate']
                        quantity = material['quantity']

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
                            bespoke_cost += float(bespoke_rate)
                    
                    new_item.cost = new_item.product.retail_price + bespoke_cost
                    new_item.save()

                    existing_item = new_item.is_duplicate()
                    print(existing_item)
                    quantity = item['quantity']
                    if not existing_item:
                        print('pass')
                        Order_Item.objects.create(order=order, item=new_item, quantity=quantity)
                    else:
                        new_item.delete()
                        Order_Item.objects.create(order=order, item=existing_item, quantity=quantity)
            order.save() 
            if original_status == "completed":
                if status != "completed":
                    order.rollback_stocks(order.get_stocks())
            else:
                if status == "completed":
                    order.deduct_stocks(order.get_stocks())
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

    return render(request, 'CLEAR/job_orders.html', {'job_orders': order_objects, 'orders':order_list, 'products':product_objects, 'accessories':accessory_objects, 'textiles':textile_objects, 'outlets':outlet_objects, 'outlet_count':outlet_count})


@login_required(login_url="/login")
@owner_required
def reports(request):
    print(request.POST)
    order_objects = Job_Order.objects.all()

    if request.method == "POST":
        reptype = request.POST.get("reptype")
        if reptype == 'materials':
            textile_objects = Textile.objects.all()
            accessory_objects = Accessory.objects.all()
            material_data = []

            
            for textile in textile_objects:
                unit = textile.get_unit_display()
                unit = unit.removeprefix("per ")

                material_data.append({'type': 'textile', 'pk': textile.material_key.material_key, 'name': textile.name, 'unit': unit, 'stock': textile.stock, 'cost': textile.cost})

            for accessory in accessory_objects:
                unit = accessory.get_unit_display()
                unit = unit.removeprefix("per ")

                if accessory.stock > 1:
                    if unit == 'inch':
                        unit = unit + "es"
                    else:
                        unit = unit + "s"

                material_data.append({'type': 'accessory', 'pk': accessory.material_key.material_key, 'name': accessory.name, 'unit': unit, 'stock': accessory.stock, 'cost': accessory.cost})

            print(material_data)


            material_data = sorted(material_data, key=lambda x: x['stock'])
            inStock_count = sum(1 for item in material_data if item['stock'] > 0)
            material_count = len(material_data)
            outStock_count = material_count - inStock_count
            datenow = timezone.now().date()
            return render(request, 'CLEAR/material_report.html', {'materials':material_data, 'today': datenow, 'stocked': inStock_count, 'unstocked': outStock_count, 'material_count': material_count, 'job_orders': order_objects})
        elif reptype == 'production':
            start_date = request.POST.get("start_date") 
            end_date = request.POST.get("end_date") 
 
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date() 
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date() 
 
            # get all objects where either file_date, start_date, or completion_date fall under the range of input dates 
            order_objects = Job_Order.objects.filter( 
                Q(file_date__range=(start_date, end_date)) | 
                Q(start_date__range=(start_date, end_date)) | 
                Q(completion_date__range=(start_date, end_date)) 
                ) 
 
            order_list = [] 
 
            bespoke_count = 0
            regular_count = 0
            for order in order_objects:
                try:
                    difference = order.completion_date - order.start_date
                    duration = difference.days
                    print(duration)
                except:
                    duration = None
                order_data = { 
                    'order': order, 
                    'file_date': order.file_date, 
                    'start_date': order.start_date,
                    'completion_date': order.completion_date, 
                    'duration': duration,
                    'status': order.order_status, 
                    'customer': order.customer, 
                    'outlet': order.outlet, 
                    'items': [], 
                    'total_price': 0
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
                        bespoke_count += 1
                    else: 
                        item_data['bespoke'] = 'no' 
                        regular_count += 1
                    item_data['item_count'] = len(item_data['materials']) 
                    order_data['items'].append(item_data) 

                    if order_item.item.cost:
                        order_data['total_price'] += order_item.item.cost*order_item.quantity
                order_data['item_count'] = len(order_data['items']) 
                order_list.append(order_data) 
            try:
                order_list = sorted(order_list, key=lambda x: x['duration'])
            except:
                pass

            if order_list:
                total_duration = sum(order_data["duration"] for order_data in order_list if order_data["duration"])
                average_duration = total_duration / len(order_list)
            else:
                average_duration = None

            file_count = 0
            start_count = 0
            complete_count = 0
            for order in order_list:
                if start_date <= order['file_date'] <= end_date:
                    file_count += 1
                if order['start_date']:
                    if start_date <= order['start_date'] <= end_date:
                        start_count += 1
                if order['completion_date']:
                    if start_date <= order['completion_date'] <= end_date:
                        complete_count += 1

            return render(request, 'CLEAR/production_report.html', {'orders': order_list, 'bespoke_count': bespoke_count, 'regular_count': regular_count, 'average_duration': average_duration, 'file_count': file_count, 'start_count': start_count, 'complete_count': complete_count, 'start_date': start_date, 'end_date': end_date, 'job_orders': order_objects})  
        elif reptype == 'pricing':
            products = Product.objects.exclude(name="test_product_test_product_test")
            table_data = []
            for product in products:
                difference = product.retail_price - product.calc_price
                days_since_last_update = (product.last_update - timezone.now().date()).days
                table_data.append({
                    'product_pk': product.pk,
                    'product_name': product.name.title(),
                    'product_retailprice': product.retail_price,
                    'product_calcprice': product.calc_price,
                    'product_difference': difference,
                    'product_dayslastupdate': days_since_last_update,
                })
            
            # Sort table_data by product_difference
            table_data_sorted = sorted(table_data, key=lambda x: x['product_difference'])
            
            return render(request, 'CLEAR/pricing_report.html', {'table_data': table_data_sorted, 'job_orders': order_objects})
        elif reptype == 'shopping_list':
            order_objects = Job_Order.objects.all()
            in_queue = [order for order in order_objects if order.order_status != 'completed' and order.order_status != 'cancelled']

            pks_str = request.POST.get("pks", "")

            pks_list = pks_str.split(",")
            pks_list = [int(pk) for pk in pks_list if pk]
            
            response = {}
            total_qty_list = []
            shoplist_data = {}

            if pks_list:
                filter_ordlist = [Job_Order.objects.get(pk=pk) for pk in pks_list]

                for ord in filter_ordlist:
                    qty_list = ord.get_stocks()
                    total_qty_list.extend(qty_list)

                for qty in total_qty_list:
                    material_id = qty['id']
                    qty_val = qty['qty']

                    if material_id in shoplist_data:
                        shoplist_data[material_id]['total_need'] += qty_val
                    else:
                        shoplist_data[material_id] = {'total_need': qty_val, 'type': qty['type']}
                
                for material_id in shoplist_data:
                    if shoplist_data[material_id]['type'] == 'textile':
                        material_object = Textile.objects.get(material_key__material_key = material_id)
                        shoplist_data[material_id]['name'] = material_object.name
                        unit = material_object.get_unit_display()
                        unit = unit.removeprefix("per ")
                        shoplist_data[material_id]['unit'] = unit

                    else:
                        material_object = Accessory.objects.get(material_key__material_key = material_id)
                        shoplist_data[material_id]['name'] = material_object.name
                        unit = material_object.get_unit_display()
                        unit = unit.removeprefix("per ")
                        shoplist_data[material_id]['unit'] = unit
                    
                    if material_object.stock >= shoplist_data[material_id]['total_need']:
                        shoplist_data[material_id]['in_stock'] = shoplist_data[material_id]['total_need']
                        shoplist_data[material_id]['to_purchase'] = 0
                    else:
                        shoplist_data[material_id]['in_stock'] = material_object.stock
                        shoplist_data[material_id]['to_purchase'] = shoplist_data[material_id]['total_need'] - material_object.stock
                    
                    shoplist_data[material_id]['total_cost'] = shoplist_data[material_id]['to_purchase']*material_object.cost
                
                material_list = []
                for material_id, material_data in shoplist_data.items():
                    info = {
                        'pk': material_id,
                        'type': material_data['type'],
                        'name': material_data['name'],
                        'unit': material_data['unit'],
                        'total_need': material_data['total_need'],
                        'in_stock': material_data['in_stock'],
                        'to_purchase': material_data['to_purchase'],
                        'total_cost': material_data['total_cost'],
                    }
                    material_list.append(info)
                
                print(material_list)
                material_list = sorted(material_list, key=lambda x: x['to_purchase'])
                response['data'] = material_list
                response['pks'] = pks_list
                return JsonResponse(response)
        
            return render(request, 'CLEAR/shopping_list.html', {'orders': in_queue}) 

    return render(request, 'CLEAR/reports.html')


def filter_stock_in(request):
    stock_in_objects = StockIn.objects.all()

    if request.method == "GET":
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')

        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        stockin_data = []
        for stockin in stock_in_objects:
            if start_date <= stockin.transaction_date <= end_date:
                formatted_date = stockin.transaction_date.strftime("%B %e, %Y").replace("  ", " ")
                stockin_data.append({
                    'stockin_pk': stockin.pk,
                    'stockin_trans_date': formatted_date,
                    'stockin_total_cost': stockin.total_cost,
                })
        return JsonResponse({'table_data' : stockin_data})


@login_required(login_url="/login")
def stock_in(request):
    order_objects = Job_Order.objects.all()

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
            response = {}
            response['status'] = True
            today = datetime.today()

            try:
                with transaction.atomic():
                    date = request.POST.get("date")
                    if not date:
                        response['status'] = False
                        response['error'] = "Please input a date"
                        raise ValueError("Please input a date")
                    if datetime.strptime(date, '%Y-%m-%d') > today:
                        response['status'] = False
                        response['error'] = "Please input a valid date"
                        raise ValueError("Please input a valid date")

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
                            if not quantity:
                                response['status'] = False
                                response['error'] = "Please input a quantity"
                                raise ValueError("Please input a date")
                            if int(quantity) == 0:
                                response['status'] = False
                                response['error'] = "Please input a quantity other than zero"
                                raise ValueError("Please input a date")
                            if not cost:
                                response['status'] = False
                                response['error'] = "Please input a cost"
                                raise ValueError("Please input a date")
                            if int(cost) < 0:
                                response['status'] = False
                                response['error'] = "Please input a non-negative cost"
                                raise ValueError("Please input a date")

                            if material_type == "textile":
                                material_object = Textile.objects.get(material_key__material_key=material_id)
                                StockIn_Textile.objects.create(textile=material_object, stock_in=new_stockIn, quantity=quantity, cost=cost)
                                material_object.stock += float(quantity)
                            else:
                                material_object = Accessory.objects.get(material_key__material_key=material_id)
                                StockIn_Accessory.objects.create(accessory=material_object, stock_in=new_stockIn, quantity=quantity, cost=cost)   
                                material_object.stock += int(quantity)
                            material_object.save()

                    new_stockIn.updateCost()
                    new_stockIn.save()

            except ValueError as e:
                print('An error occurred:', str(e))


            response['msg'] = "Form submitted."
            response['url'] = reverse('stock_in')

            # return dict to ajax
            return JsonResponse(response)
        
        elif action == 'edit_form':
            response = {}
            response['status'] = True
            today = datetime.today()
            print('edit')
            try:
                with transaction.atomic():
                    date = request.POST.get("date")
                    pk = request.POST.get("pk")
                    if not date:
                        response['status'] = False
                        response['error'] = "Please input a date"
                        raise ValueError("Please input a date")
                    if datetime.strptime(date, '%Y-%m-%d') > today:
                        response['status'] = False
                        response['error'] = "Please input a valid date"
                        raise ValueError("Please input a valid date")

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
                            if not quantity:
                                response['status'] = False
                                response['error'] = "Please input a quantity"
                                raise ValueError("Please input a date")
                            if int(quantity) == 0:
                                response['status'] = False
                                response['error'] = "Please input a quantity other than zero"
                                raise ValueError("Please input a date")
                            if not cost:
                                response['status'] = False
                                response['error'] = "Please input a cost"
                                raise ValueError("Please input a date")
                            if int(cost) < 0:
                                response['status'] = False
                                response['error'] = "Please input a non-negative cost"
                                raise ValueError("Please input a date")
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

            except ValueError as e:
                print('An error occurred:', str(e))

            response['msg'] = "Form submitted."
            response['url'] = reverse('stock_in')

            # return dict to ajax
            return JsonResponse(response)
        elif 'delete_form' in request.POST:
            pk = request.POST.get("pk")
            StockIn.objects.filter(pk=pk).delete()
            return redirect('stock_in')



    return render(request, 'CLEAR/stock_in.html', {'textiles':textile_objects, 'accessories': accessory_objects, 'stock_ins':stockIn_material_list, 'job_orders': order_objects})


@login_required(login_url="/login")
@owner_required
def manage_accounts(request):
    account_objects = Account.objects.all()

    return render(request, 'CLEAR/manage_accounts.html', {'account_objects' : account_objects})

def sign_up(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data['role']
            account = Account.objects.create(user=user, role=role)
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


def delete_user(request, user_id):
    if request.method == 'POST':
        user = User.objects.get(pk=user_id)
        user.delete()

    return redirect('manage_accounts') 


def search_users(request):
    account_objects = Account.objects.all()
    search_query = request.GET.get('q')

    if search_query:
        account_objects = account_objects.filter(
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(role__icontains=search_query)
        )

        table_data = []
        for account in account_objects:
            table_data.append({
                'user_pk': account.user.pk,
                'username': account.user.username,
                'first_name': account.user.first_name,
                'last_name': account.user.last_name,
                'role': account.role
            })
    return JsonResponse({'table_data': table_data})




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

def dynamic_pricing(request):
    print('back end entered')
    print(request.GET)
    response = {}
    response['status'] = True
    try:
        with transaction.atomic():
            prod_margin = request.GET.get("margin")
            labor_time = request.GET.get("labor")
            misc_margin = request.GET.get("misc")

            print(prod_margin, labor_time, misc_margin)

            if Product.objects.filter(name="test_product_test_product_test").exists():
                test_product = Product.objects.get(name="test_product_test_product_test")

                test_product.prod_margin = prod_margin
                test_product.labor_time = labor_time
                test_product.misc_margin = misc_margin
            else:
                test_product = Product.objects.create(name="test_product_test_product_test", 
                                            prod_margin=prod_margin, 
                                            labor_time=labor_time, 
                                            misc_margin=misc_margin)
                
            Product_Component.objects.filter(product=test_product).delete()

            textile_data = json.loads(request.GET.get("textile_data"))
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

                            if height and width and component_quantity:
                                if existing_component:
                                    product_component = Product_Component.objects.create(product=test_product, textile=textile_object, component=existing_component, height=height, width=width, quantity=component_quantity, buffer=buffer)
                                else:
                                    new_component = Component.objects.create(component_name=component_name)
                                    product_component = Product_Component.objects.create(product=test_product, textile=textile_object, component=new_component, height=height, width=width, quantity=component_quantity, buffer=buffer)

            Product_Accessory.objects.filter(product=test_product).delete()
            accessory_data = json.loads(request.GET.get("accessory_data"))
            for accessory in accessory_data:
                accessory_id = accessory['accessory_id']
                quantity = accessory['quantity']

                if accessory_id == "delete":
                    pass
                else:
                    if quantity:
                        accessory_object = Accessory.objects.get(material_key__material_key=accessory_id)
                        Product_Accessory.objects.create(product=test_product, accessory=accessory_object, accessory_quantity=quantity)
            
            calc_price = "{:.2f}".format(test_product.updateCost('update'))
            test_product.save()

            print(calc_price)

            if response['status'] == False:
                raise Exception("An error has occured during the transaction")
    except:
        print('failed')
        calc_price = ""
    return JsonResponse({'calc_price':calc_price})

def download_matrep(request):
    textile_objects = Textile.objects.all()
    accessory_objects = Accessory.objects.all()
    material_data = []

    for textile in textile_objects:
        unit = textile.get_unit_display()
        unit = unit.removeprefix("per ")

        material_data.append({'pk': textile.material_key.material_key, 'type': 'textile', 'name': textile.name, 'cost': textile.cost, 'stock': textile.stock, 'unit': unit})

    for accessory in accessory_objects:
        unit = accessory.get_unit_display()
        unit = unit.removeprefix("per ")

        if accessory.stock > 1:
            if unit == 'inch':
                unit = unit + "es"
            else:
                unit = unit + "s"

        material_data.append({'pk': accessory.material_key.material_key, 'type': 'accessory', 'name': accessory.name, 'cost': accessory.cost, 'stock': accessory.stock, 'unit': unit})

    df = pd.DataFrame(material_data)

    excel_filename = 'material_data.xlsx'

    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)

    # Set response headers
    response = FileResponse(excel_buffer, as_attachment=True, filename=excel_filename)
    return response

def download_prodrep(request):
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    print(request.GET)

    start_date = datetime.strptime(start_date, '%B %d, %Y').date() 
    end_date = datetime.strptime(end_date, '%B %d, %Y').date() 

    # get all objects where either file_date, start_date, or completion_date fall under the range of input dates 
    order_objects = Job_Order.objects.filter( 
        Q(file_date__range=(start_date, end_date)) | 
        Q(start_date__range=(start_date, end_date)) | 
        Q(completion_date__range=(start_date, end_date)) 
        ) 

    order_list = [] 
    for order in order_objects:
        try:
            difference = order.completion_date - order.start_date
            duration = difference.days
            print(duration)
        except:
            duration = "None"
        order_data = { 
            'pk': order.pk, 
            'file_date': str(order.file_date), 
            'start_date': str(order.start_date),
            'completion_date': str(order.completion_date), 
            'duration': duration,
            'status': order.order_status, 
            'customer': order.customer, 
            'outlet': order.outlet.outlet_name, 
            'total_price': 0
        } 
        for order_item in order.order_item_set.all(): 
            if order_item.item.cost:
                order_data['total_price'] += order_item.item.cost*order_item.quantity
        order_list.append(order_data)

    df = pd.DataFrame(order_list)

    excel_filename = 'production_report.xlsx'

    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)

    print(df)

    response = FileResponse(excel_buffer, as_attachment=True, filename=excel_filename)
    print(response)
    return response

def download_pricerep(request):
    products = Product.objects.exclude(name="test_product_test_product_test")
    table_data = []
    for product in products:
        difference = product.retail_price - product.calc_price
        days_since_last_update = (product.last_update - timezone.now().date()).days
        table_data.append({
            'pk': product.pk,
            'name': product.name.title(),
            'retailprice': product.retail_price,
            'calcprice': product.calc_price,
            'difference': difference,
            'dayslastupdate': days_since_last_update,
        })
    
    # Sort table_data by product_difference
    table_data_sorted = sorted(table_data, key=lambda x: x['difference'])

    df = pd.DataFrame(table_data_sorted)

    excel_filename = 'pricing_report.xlsx'

    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)

    print(df)

    response = FileResponse(excel_buffer, as_attachment=True, filename=excel_filename)
    return response

def download_shoplist(request):
    pks_str = request.GET.get("pks", "")

    pks_list = pks_str.split(",")
    pks_list = [int(pk) for pk in pks_list if pk]
    
    total_qty_list = []
    shoplist_data = {}


    if pks_list:
        filter_ordlist = [Job_Order.objects.get(pk=pk) for pk in pks_list]

        for ord in filter_ordlist:
            qty_list = ord.get_stocks()
            total_qty_list.extend(qty_list)

        for qty in total_qty_list:
            material_id = qty['id']
            qty_val = qty['qty']

            if material_id in shoplist_data:
                shoplist_data[material_id]['total_need'] += qty_val
            else:
                shoplist_data[material_id] = {'total_need': qty_val, 'type': qty['type']}
        
        for material_id in shoplist_data:
            if shoplist_data[material_id]['type'] == 'textile':
                material_object = Textile.objects.get(material_key__material_key = material_id)
                shoplist_data[material_id]['name'] = material_object.name
                unit = material_object.get_unit_display()
                unit = unit.removeprefix("per ")
                shoplist_data[material_id]['unit'] = unit
            else:
                material_object = Accessory.objects.get(material_key__material_key = material_id)
                shoplist_data[material_id]['name'] = material_object.name
                unit = material_object.get_unit_display()
                unit = unit.removeprefix("per ")
                shoplist_data[material_id]['unit'] = unit

            
            if material_object.stock >= shoplist_data[material_id]['total_need']:
                shoplist_data[material_id]['in_stock'] = shoplist_data[material_id]['total_need']
                shoplist_data[material_id]['to_purchase'] = 0
            else:
                shoplist_data[material_id]['in_stock'] = material_object.stock
                shoplist_data[material_id]['to_purchase'] = shoplist_data[material_id]['total_need'] - material_object.stock
            
            shoplist_data[material_id]['total_cost'] = shoplist_data[material_id]['to_purchase']*material_object.cost
        
        material_list = []
        for material_id, material_data in shoplist_data.items():
            info = {
                'pk': material_id,
                'type': material_data['type'],
                'name': material_data['name'],
                'unit': material_data['unit'],
                'total_need': material_data['total_need'],
                'in_stock': material_data['in_stock'],
                'to_purchase': material_data['to_purchase'],
                'total_cost': material_data['total_cost'],
            }
            material_list.append(info)
        
        print(material_list)
        material_list = sorted(material_list, key=lambda x: x['to_purchase'])

    df = pd.DataFrame(material_list)

    excel_filename = 'shopping_list.xlsx'

    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)

    response = FileResponse(excel_buffer, as_attachment=True, filename=excel_filename)
    print(response)
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

