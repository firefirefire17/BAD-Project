from django.http import HttpResponseForbidden
from functools import wraps
from .models import Account

def owner_required(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        try:
            account = Account.objects.get(username=request.user.username)
            if account.role == Account.ROLE_OWNER:
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponseForbidden("You don't have permission to access this page.")
        except Account.DoesNotExist:
            return HttpResponseForbidden("You don't have permission to access this page.")
    return wrapped_view

def product_manager_required(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        try:
            account = Account.objects.get(username=request.user.username)
            if account.role == Account.ROLE_PRODUCT_MANAGER:
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponseForbidden("You don't have permission to access this page.")
        except Account.DoesNotExist:
            return HttpResponseForbidden("You don't have permission to access this page.")
    return wrapped_view