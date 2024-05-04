"""
URL configuration for msys42 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard, name="dashboard"),
    path('orders/', views.job_orders, name="orders"),
    path('products/', views.products, name="products"),
    path('materials/', views.materials, name="materials"),
    path('reports/', views.reports, name="reports"),
    path('reports/material/', views.material_report, name="material_report"),
    path('reports/production/', views.production_report, name="production_reports"),
    path('reports/pricing/', views.pricing_report, name="pricing_reports"),
    path('reports/shopping_list/', views.shopping_list, name="shopping_list_reports"),
    path('sign-up/', views.sign_up, name="sign_up"),
    path('login/', views.login_view, name ="login"),
    path('logout/', views.logout_view, name="logout"),
    path('stock_in/', views.stock_in, name="stock_in"),
    path('get_material_options/', views.get_material_options, name='get_material_options'),
    path('dynamic_pricing/', views.dynamic_pricing, name='dynamic_pricing'),
    path('filter_materials/', views.filter_materials, name="filter_materials"),
    path('search_products/', views.search_products, name="search_products"),
    path('download_matrep/', views.download_matrep, name="download_matrep"),
    path('download_prodrep/', views.download_matrep, name="download_matrep"),
    path('search_joborders', views.search_joborders, name="search_joborders"),
]
