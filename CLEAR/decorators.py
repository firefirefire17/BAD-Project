from django.http import HttpResponseForbidden
from functools import wraps
from .models import Account
from django.shortcuts import redirect
from django.contrib import messages

def owner_required(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            try:
                account = Account.objects.get(user=request.user)
                if account.role == Account.ROLE_OWNER:
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(request, "You don't have permission to access this page.")
                    return redirect('dashboard')
            except Account.DoesNotExist:
                messages.error(request, "You don't have permission to access this page.")
                return redirect('dashboard')
        else:
            messages.error(request, "You don't have permission to access this page.")
            return redirect('dashboard')
    return wrapped_view
