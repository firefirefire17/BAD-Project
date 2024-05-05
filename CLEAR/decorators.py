from django.http import HttpResponseForbidden
from functools import wraps
from .models import Account

def owner_required(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            try:
                account = Account.objects.get(user=request.user)
                if account.role == Account.ROLE_OWNER:
                    return view_func(request, *args, **kwargs)
                else:
                    return HttpResponseForbidden("You don't have permission to access this page.")
            except Account.DoesNotExist:
                return HttpResponseForbidden("You don't have permission to access this page.")
        else:
            return HttpResponseForbidden("You don't have permission to access this page.")
    return wrapped_view
