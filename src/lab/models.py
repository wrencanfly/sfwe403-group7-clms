import uuid
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

ROLES = [(x, x.title()) for x in ['manager', 'collector', 'technician', 'cashier', 'patient', 'provider']]
STAFF_ROLES = ('manager', 'collector', 'technician', 'cashier')

class Account(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLES)
    must_change_password = models.BooleanField(default=True)
    failures = models.PositiveIntegerField(default=0)
    locked = models.BooleanField(default=False)

class Patient(models.Model):
    name = models.CharField(max_length=120)
    dob = models.DateField('Date of birth')
    gender = models.CharField(max_length=30)
    address = models.CharField(max_length=250)
    phone = models.CharField(max_length=40)
    email = models.EmailField()
    insurance_provider = models.CharField(max_length=120)
    policy_number = models.CharField(max_length=80)
    coverage = models.CharField(max_length=200)
    active = models.BooleanField(default=True)
    def __str__(self): return f'P{self.pk:04d} · {self.name}'

class Lot(models.Model):
    item = models.CharField(max_length=120)
    lot = models.CharField(max_length=80, unique=True)
    test_code = models.CharField(max_length=40)
    instrument = models.CharField(max_length=120)
    quantity = models.PositiveIntegerField()
    full_stock = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    expiry = models.DateField()
    @property
    def expired(self): return self.expiry < timezone.localdate()
    def __str__(self): return f'{self.item} · {self.lot} · {self.quantity} units'

class Order(models.Model):
    report_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT)
    route = models.CharField(max_length=20, choices=[('walk-in','Walk-in'),('telephone','Telephone')])
    physician_id = models.CharField(max_length=60)
    physician_name = models.CharField(max_length=120)
    physician_contact = models.CharField(max_length=160)
    insurance_provider = models.CharField(max_length=120)
    policy_number = models.CharField(max_length=80)
    coverage = models.CharField(max_length=200)
    test_code = models.CharField(max_length=40)
    test_name = models.CharField(max_length=120)
    sample_type = models.CharField(max_length=40, choices=[('blood','Blood'),('urine','Urine'),('tissue','Tissue')])
    # Fields reserved for the next release's result workflow.
    result_value = models.CharField(max_length=120, blank=True)
    units = models.CharField(max_length=40, blank=True)
    reference_range = models.CharField(max_length=120, blank=True)
    result_status = models.CharField(max_length=20, default='pending')
    results_received = models.DateTimeField(null=True, blank=True)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='performed_orders')
    instrument = models.CharField(max_length=120, blank=True)
    def __str__(self): return f'T{self.pk:04d} · {self.test_name}'

class Sample(models.Model):
    order = models.OneToOneField(Order, on_delete=models.PROTECT)
    barcode = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    lot = models.ForeignKey(Lot, on_delete=models.PROTECT)
    collector = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    collected = models.DateTimeField(auto_now_add=True)
    label_issued = models.DateTimeField(null=True, blank=True)

class Event(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=80)
    record = models.CharField(max_length=120)
    detail = models.TextField(blank=True)
    at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['-at']

class LabProfile(models.Model):
    name = models.CharField(max_length=120, default='Group 7 Clinical Laboratory')
    website = models.URLField(default='https://example.invalid')
    address = models.CharField(max_length=200, default='Classroom demonstration')
    owner = models.CharField(max_length=120, default='Group 7')
    phone = models.CharField(max_length=40, default='555-0100')
    working_hours = models.CharField(max_length=120, default='Monday to Friday, 8 am to 5 pm')
