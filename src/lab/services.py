from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from .models import Order, Lot, Sample, Event

@transaction.atomic
def collect(order_id, lot_id, actor):
    if actor.account.role != 'collector': raise ValidationError('Only specimen collectors can collect samples.')
    order=Order.objects.select_for_update().get(pk=order_id)
    if Sample.objects.filter(order=order).exists(): raise ValidationError('This order already has a sample. No stock was deducted.')
    if not order.patient.active: raise ValidationError('This patient is archived.')
    # Conditional SQL update prevents negative stock and expiry bypass even if data changes after form load.
    changed=Lot.objects.filter(pk=lot_id,test_code=order.test_code,expiry__gte=timezone.localdate(),quantity__gte=1).update(quantity=F('quantity')-1)
    if changed != 1: raise ValidationError('Collection blocked: supply is expired, unavailable, or does not match this test.')
    sample=Sample.objects.create(order=order,lot_id=lot_id,collector=actor)
    Event.objects.create(actor=actor,action='Sample collected',record=f'Order {order.pk}',detail=f'Barcode {sample.barcode}; lot {lot_id}; quantity -1')
    return sample

@transaction.atomic
def issue_label(sample_id, actor):
    if actor.account.role != 'collector': raise ValidationError('Only specimen collectors can issue labels.')
    now=timezone.now()
    changed=Sample.objects.filter(pk=sample_id,label_issued__isnull=True).update(label_issued=now)
    if changed != 1: raise ValidationError('A label has already been issued for this sample.')
    sample=Sample.objects.get(pk=sample_id)
    Event.objects.create(actor=actor,action='Barcode label issued',record=f'Order {sample.order_id}',detail=str(sample.barcode))
    return sample
