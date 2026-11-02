from django.shortcuts import redirect
from .models import Account

class PasswordGate:
    def __init__(self, get_response): self.get_response = get_response
    def __call__(self, request):
        if request.user.is_authenticated and request.path not in ['/password/', '/logout/']:
            if Account.objects.filter(user=request.user, must_change_password=True).exists():
                return redirect('password')
        return self.get_response(request)
