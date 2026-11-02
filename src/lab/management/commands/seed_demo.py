import os
from datetime import timedelta
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from lab.models import Account, Patient, Lot, Order, LabProfile, ROLES

class Command(BaseCommand):
    help='Create fictional classroom fixtures without overwriting existing data or passwords.'
    def handle(self,*args,**kwargs):
        password=os.environ.get('CLMS_DEMO_PASSWORD')
        if not password or len(password)<12:
            raise CommandError('Set CLMS_DEMO_PASSWORD to a local password of at least 12 characters.')
        for name,_ in ROLES:
            user,created=User.objects.get_or_create(username=name,defaults={'email':f'{name}@example.invalid'})
            if created: user.set_password(password);user.save()
            Account.objects.get_or_create(user=user,defaults={'role':name,'must_change_password':False})
        LabProfile.objects.get_or_create(pk=1)
        p,_=Patient.objects.get_or_create(name='Alex Morgan',email='alex@example.invalid',defaults={'dob':'1995-04-12','gender':'Not specified','address':'100 Example Avenue','phone':'555-0101','insurance_provider':'Example Health','policy_number':'DEMO-001','coverage':'Classroom test coverage'})
        today=timezone.localdate()
        for lot,days,qty in [('CBC-2026-A',120,24),('CBC-EXPIRED',-1,8),('CBC-EMPTY',120,0)]:
            Lot.objects.get_or_create(lot=lot,defaults={'item':'CBC collection kit','test_code':'CBC','instrument':'Analyzer A','quantity':qty,'full_stock':100,'expiry':today+timedelta(days=days)})
        Order.objects.get_or_create(report_id='963d167c-ea56-4e54-9485-4ca8d44b9472',defaults={'patient':p,'test_code':'CBC','route':'walk-in','physician_id':'DEMO-MD-01','physician_name':'Dr Taylor Reed','physician_contact':'physician@example.invalid','insurance_provider':p.insurance_provider,'policy_number':p.policy_number,'coverage':p.coverage,'test_name':'Complete blood count','sample_type':'blood','units':'10^9/L','reference_range':'4.0–11.0'})
        self.stdout.write(self.style.SUCCESS('Fictional demo records are ready. Existing passwords and records were preserved.'))
