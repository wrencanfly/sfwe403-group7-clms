from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from .models import Patient, Lot, Order, LabProfile, ROLES, STAFF_ROLES

class NewPasswordForm(PasswordChangeForm):
    def clean_new_password1(self):
        password = self.cleaned_data['new_password1']
        if self.user.check_password(password):
            raise forms.ValidationError('Choose a new password different from your current password.')
        return password

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

class StaffForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    role = forms.ChoiceField(choices=[r for r in ROLES if r[0] in STAFF_ROLES])
    temporary_password = forms.CharField(widget=forms.PasswordInput, validators=[validate_password])
    def clean_username(self):
        name=self.cleaned_data['username']
        if User.objects.filter(username=name).exists(): raise forms.ValidationError('Username already exists.')
        return name

class PatientForm(forms.ModelForm):
    class Meta:
        model=Patient
        exclude=['active']
        widgets={'dob':forms.DateInput(attrs={'type':'date'})}
    def clean_dob(self):
        d=self.cleaned_data['dob']
        if d>timezone.localdate(): raise forms.ValidationError('Date of birth cannot be in the future.')
        return d

class LotForm(forms.ModelForm):
    reason=forms.CharField(max_length=200, help_text='Required explanation for the inventory record or adjustment.')
    class Meta:
        model=Lot
        fields=['item','lot','test_code','instrument','quantity','full_stock','expiry']
        widgets={'expiry':forms.DateInput(attrs={'type':'date'})}

class OrderForm(forms.ModelForm):
    class Meta:
        model=Order
        fields=['patient','route','physician_id','physician_name','physician_contact','insurance_provider','policy_number','coverage','test_code','test_name','sample_type','units','reference_range']
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['patient'].queryset=Patient.objects.filter(active=True).order_by('name')

class ProfileForm(forms.ModelForm):
    class Meta:
        model=LabProfile
        fields='__all__'

class CollectionForm(forms.Form):
    lot=forms.ModelChoiceField(queryset=Lot.objects.none())
    def __init__(self,*args,order,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['lot'].queryset=Lot.objects.filter(test_code=order.test_code).order_by('expiry')
