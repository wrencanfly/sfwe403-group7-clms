from functools import wraps
from io import BytesIO
import barcode
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Account, Patient, Lot, Order, Sample, Event, LabProfile, STAFF_ROLES
from .forms import LoginForm, NewPasswordForm, StaffForm, PatientForm, LotForm, OrderForm, ProfileForm, CollectionForm
from .services import collect, issue_label

def role(user):
    return Account.objects.filter(user=user).values_list('role',flat=True).first() if user.is_authenticated else None

def navigation(request):
    r=role(request.user)
    return {'role':r,'is_lab_staff':r in STAFF_ROLES}

def allowed(*roles):
    def wrap(fn):
        @login_required
        @wraps(fn)
        def inner(request,*args,**kwargs):
            if role(request.user) not in roles:
                Event.objects.create(actor=request.user,action='Access denied',record=request.path)
                return HttpResponseForbidden('Your role cannot access this function.')
            return fn(request,*args,**kwargs)
        return inner
    return wrap

def form_page(request,title,form):
    return render(request,'lab/form.html',{'title':title,'form':form})

def sign_in(request):
    if request.user.is_authenticated: return redirect('home')
    form=LoginForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        authenticated=None
        with transaction.atomic():
            acct=Account.objects.select_for_update().select_related('user').filter(user__username=form.cleaned_data['username']).first()
            if acct and not acct.locked and acct.user.is_active:
                if acct.user.check_password(form.cleaned_data['password']):
                    acct.failures=0
                    authenticated=acct.user
                else:
                    acct.failures+=1
                    if acct.failures>=5:
                        acct.locked=True
                        recipients=list(User.objects.filter(account__role='manager',is_active=True).exclude(email='').values_list('email',flat=True))
                        transaction.on_commit(lambda:send_mail('CLMS account locked',f'Account {acct.user.username} requires manager recovery.',None,recipients))
                acct.save(update_fields=['failures','locked'])
            if authenticated:
                login(request,authenticated)
                Event.objects.create(actor=authenticated,action='Signed in',record='Account')
            else:
                # Do not store submitted credentials or reveal whether an account exists.
                Event.objects.create(action='Failed sign in',record='Account')
        if authenticated: return redirect('home')
        form.add_error(None,'Sign in failed. Check credentials or contact your manager for account recovery.')
    return form_page(request,'Sign in to your laboratory',form)

@login_required
@require_POST
def sign_out(request):
    Event.objects.create(actor=request.user,action='Signed out',record='Account')
    logout(request)
    return redirect('login')

@login_required
def password(request):
    form=NewPasswordForm(request.user,request.POST or None)
    if request.method=='POST' and form.is_valid():
        user=form.save()
        Account.objects.filter(user=user).update(must_change_password=False)
        update_session_auth_hash(request,user)
        Event.objects.create(actor=user,action='Password changed',record='Account')
        messages.success(request,'Password updated.')
        return redirect('home')
    return form_page(request,'Change your password',form)

@login_required
def home(request):
    staff=role(request.user) in STAFF_ROLES
    return render(request,'lab/home.html',{'profile':LabProfile.objects.first(),'patient_count':Patient.objects.filter(active=True).count() if staff else None,'order_count':Order.objects.count() if staff else None,'sample_count':Sample.objects.count() if staff else None,'recent':Order.objects.select_related('patient').order_by('-created')[:6] if staff else []})

@allowed('manager')
def accounts(request):
    form=StaffForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            user=User.objects.create_user(form.cleaned_data['username'],form.cleaned_data['email'],form.cleaned_data['temporary_password'])
            Account.objects.create(user=user,role=form.cleaned_data['role'])
            Event.objects.create(actor=request.user,action='Staff account created',record=user.username,detail=form.cleaned_data['role'])
        messages.success(request,'Account created. A password change is required at first sign in.')
        return redirect('accounts')
    return render(request,'lab/accounts.html',{'title':'Staff and account recovery','form':form,'accounts':Account.objects.select_related('user').all()})

@allowed('manager')
@require_POST
def unlock(request,pk):
    a=get_object_or_404(Account,pk=pk)
    a.locked=False;a.failures=0;a.save(update_fields=['locked','failures'])
    Event.objects.create(actor=request.user,action='Account unlocked',record=a.user.username)
    messages.success(request,'Account unlocked.')
    return redirect('accounts')

@allowed(*STAFF_ROLES)
def patients(request):
    q=request.GET.get('q','')
    return render(request,'lab/patients.html',{'patients':Patient.objects.filter(active=True,name__icontains=q).order_by('name'),'q':q})

@allowed(*STAFF_ROLES)
def patient_edit(request,pk=None):
    patient=get_object_or_404(Patient,pk=pk,active=True) if pk else None
    form=PatientForm(request.POST or None,instance=patient)
    if request.method=='POST' and form.is_valid():
        obj=form.save()
        Event.objects.create(actor=request.user,action='Patient profile saved',record=f'Patient {obj.pk}')
        messages.success(request,'Patient profile saved.')
        return redirect('patient_detail',pk=obj.pk)
    return form_page(request,'Edit patient' if pk else 'Create patient',form)

@allowed(*STAFF_ROLES)
def patient_detail(request,pk):
    patient=get_object_or_404(Patient,pk=pk)
    return render(request,'lab/patient.html',{'patient':patient,'orders':Order.objects.filter(patient=patient).select_related('sample','sample__collector').order_by('-created')})

@allowed('manager','collector')
@require_POST
def archive_patient(request,pk):
    patient=get_object_or_404(Patient,pk=pk)
    patient.active=False;patient.save(update_fields=['active'])
    Event.objects.create(actor=request.user,action='Patient archived',record=f'Patient {pk}')
    messages.success(request,'Patient archived. Existing test history is retained.')
    return redirect('patients')

@allowed('manager','collector')
def inventory(request):
    return render(request,'lab/inventory.html',{'lots':Lot.objects.order_by('expiry')})

@allowed('manager')
def lot_edit(request,pk=None):
    lot=get_object_or_404(Lot,pk=pk) if pk else None
    old_qty=lot.quantity if lot else 0
    form=LotForm(request.POST or None,instance=lot)
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            if pk:
                # Prevent an adjustment overwriting concurrent collection consumption.
                changed=Lot.objects.filter(pk=pk,quantity=old_qty).update(**{k:v for k,v in form.cleaned_data.items() if k!='reason'})
                if not changed:
                    form.add_error(None,'Stock changed while saving. Reload and retry.')
                    return form_page(request,'Update inventory',form)
                obj=lot
            else: obj=form.save()
            Event.objects.create(actor=request.user,action='Inventory adjusted',record=f'Lot {obj.pk}',detail=f'{old_qty} to {obj.quantity}; {form.cleaned_data["reason"]}')
        messages.success(request,'Inventory saved.')
        return redirect('inventory')
    return form_page(request,'Update inventory' if pk else 'Add inventory lot',form)

@allowed(*STAFF_ROLES)
def orders(request):
    return render(request,'lab/orders.html',{'orders':Order.objects.select_related('patient','sample').order_by('-created')})

@allowed(*STAFF_ROLES)
def order_new(request):
    form=OrderForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        obj=form.save()
        Event.objects.create(actor=request.user,action='Test order entered',record=f'Order {obj.pk}',detail=obj.route)
        return redirect('order_detail',pk=obj.pk)
    return form_page(request,'Enter a test request',form)

@allowed(*STAFF_ROLES)
def order_detail(request,pk):
    order=get_object_or_404(Order.objects.select_related('patient'),pk=pk)
    return render(request,'lab/order.html',{'order':order,'sample':Sample.objects.filter(order=order).select_related('collector','lot').first(),'events':Event.objects.filter(record=f'Order {pk}')})

@allowed('collector')
def collection(request,pk):
    order=get_object_or_404(Order,pk=pk)
    form=CollectionForm(request.POST or None,order=order)
    if request.method=='POST' and form.is_valid():
        try:
            collect(pk,form.cleaned_data['lot'].pk,request.user)
            messages.success(request,'Sample collected and one inventory unit consumed.')
            return redirect('order_detail',pk=pk)
        except ValidationError as e: form.add_error(None,e)
    return form_page(request,f'Check supplies and collect for {order}',form)

@allowed('collector')
@require_POST
def label(request,pk):
    sample=get_object_or_404(Sample,pk=pk)
    try: sample=issue_label(sample.pk,request.user)
    except ValidationError as e:
        messages.error(request,' '.join(e.messages));return redirect('order_detail',pk=sample.order_id)
    buffer=BytesIO()
    barcode.get('code128',str(sample.barcode)).write(buffer,options={'module_width':0.18,'module_height':12,'font_size':8})
    response=render(request,'lab/label.html',{'sample':sample,'barcode_svg':buffer.getvalue().decode().split('?>',1)[-1]})
    response['Cache-Control']='no-store'
    return response

@login_required
def profile(request):
    obj=LabProfile.objects.first()
    if request.method=='POST' and role(request.user)!='manager': return HttpResponseForbidden()
    form=ProfileForm(request.POST or None,instance=obj)
    if request.method=='POST' and form.is_valid():
        form.save();messages.success(request,'Laboratory profile saved.');return redirect('profile')
    return render(request,'lab/profile.html',{'profile':obj,'form':form})
