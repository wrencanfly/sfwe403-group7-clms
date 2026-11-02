from datetime import timedelta
from io import StringIO
from unittest.mock import patch
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Account, Patient, Lot, Order, Sample, Event, ROLES
from .services import collect, issue_label

class WorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for role,_ in ROLES:
            u=User.objects.create_user(role,email=f'{role}@example.invalid',password='Test-only-strong-pass')
            Account.objects.create(user=u,role=role,must_change_password=False)
        cls.patient=Patient.objects.create(name='Fictional patient',dob='1990-01-01',gender='Unspecified',address='Example',phone='555-0100',email='p@example.invalid',insurance_provider='Example',policy_number='TEST1',coverage='Test')
        cls.order=Order.objects.create(patient=cls.patient,route='telephone',physician_id='D1',physician_name='Example physician',physician_contact='555-0102',insurance_provider='Example',policy_number='TEST1',coverage='Test',test_code='CBC',test_name='CBC',sample_type='blood')
        cls.lot=Lot.objects.create(item='Kit',lot='L1',test_code='CBC',instrument='A',quantity=2,full_stock=10,expiry=timezone.localdate()+timedelta(days=2))
    def user(self,role): return User.objects.get(username=role)
    def sign(self,role): self.client.force_login(self.user(role))
    def test_six_role_access_matrix(self):
        for r,_ in ROLES:
            self.sign(r)
            self.assertEqual(self.client.get('/patients/').status_code,200 if r in ['manager','collector','technician','cashier'] else 403)
            self.assertEqual(self.client.get('/accounts/').status_code,200 if r=='manager' else 403)
            self.assertEqual(self.client.get('/inventory/').status_code,200 if r in ['manager','collector'] else 403)
            self.assertEqual(self.client.get('/orders/1/collect/').status_code,200 if r=='collector' else 403)
            self.client.logout()
    def test_first_login_forces_password_change(self):
        Account.objects.filter(user=self.user('collector')).update(must_change_password=True)
        self.sign('collector')
        self.assertRedirects(self.client.get('/patients/'),'/password/')
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_five_failures_lock_and_notify_manager(self):
        with self.captureOnCommitCallbacks(execute=True):
            for _ in range(5): self.client.post('/login/',{'username':'collector','password':'wrong'})
        a=Account.objects.get(user=self.user('collector'))
        self.assertTrue(a.locked);self.assertEqual(a.failures,5)
        self.assertEqual(len(mail.outbox),1);self.assertIn('manager@example.invalid',mail.outbox[0].to)
        self.client.post('/login/',{'username':'collector','password':'Test-only-strong-pass'})
        self.assertNotIn('_auth_user_id',self.client.session)
        self.sign('technician');self.assertEqual(self.client.post(f'/accounts/{a.pk}/unlock/').status_code,403)
        self.sign('manager');self.client.post(f'/accounts/{a.pk}/unlock/')
        a.refresh_from_db();self.assertFalse(a.locked)
    def test_success_resets_consecutive_failures(self):
        for _ in range(4): self.client.post('/login/',{'username':'collector','password':'wrong'})
        self.client.post('/login/',{'username':'collector','password':'Test-only-strong-pass'})
        self.assertEqual(Account.objects.get(user=self.user('collector')).failures,0)
    def test_collection_consumes_once_and_logs(self):
        s=collect(self.order.pk,self.lot.pk,self.user('collector'))
        self.lot.refresh_from_db();self.assertEqual(self.lot.quantity,1)
        with self.assertRaises(ValidationError): collect(self.order.pk,self.lot.pk,self.user('collector'))
        self.lot.refresh_from_db();self.assertEqual(self.lot.quantity,1)
        self.assertEqual(Sample.objects.count(),1)
        self.assertTrue(Event.objects.filter(action='Sample collected',record='Order 1').exists())
        self.assertEqual(s.collector.username,'collector')
    def test_expired_empty_and_wrong_test_block_collection(self):
        for changes in [{'expiry':timezone.localdate()-timedelta(days=1)},{'quantity':0},{'test_code':'OTHER'}]:
            Lot.objects.filter(pk=self.lot.pk).update(quantity=2,expiry=timezone.localdate()+timedelta(days=2),test_code='CBC',**{})
            Lot.objects.filter(pk=self.lot.pk).update(**changes)
            with self.assertRaises(ValidationError): collect(self.order.pk,self.lot.pk,self.user('collector'))
            self.assertEqual(Sample.objects.count(),0)
    def test_noncollector_cannot_collect_or_issue_label(self):
        for r in ['manager','technician','cashier','patient','provider']:
            with self.assertRaises(ValidationError): collect(self.order.pk,self.lot.pk,self.user(r))
    def test_label_issued_once_and_post_only(self):
        s=collect(self.order.pk,self.lot.pk,self.user('collector'))
        self.sign('collector')
        self.assertEqual(self.client.get(f'/samples/{s.pk}/label/').status_code,405)
        response=self.client.post(f'/samples/{s.pk}/label/')
        self.assertContains(response,'<svg')
        with self.assertRaises(ValidationError): issue_label(s.pk,self.user('collector'))
    def test_patient_archive_preserves_order_and_blocks_collection(self):
        self.sign('technician');self.assertEqual(self.client.post('/patients/1/archive/').status_code,403)
        self.sign('manager');self.assertEqual(self.client.post('/patients/1/archive/').status_code,302)
        self.patient.refresh_from_db();self.assertFalse(self.patient.active)
        self.assertEqual(Order.objects.count(),1)
        self.assertContains(self.client.get('/patients/1/'),'CBC')
        with self.assertRaises(ValidationError): collect(self.order.pk,self.lot.pk,self.user('collector'))
    def test_order_required_fields_and_pending_state(self):
        self.sign('cashier')
        self.client.post('/orders/new/',{'patient':1,'test_name':'CBC'})
        self.assertEqual(Order.objects.count(),1)
        self.assertEqual(self.order.result_status,'pending')
    def test_manager_inventory_rejects_negative(self):
        self.sign('manager')
        self.client.post('/inventory/new/',{'item':'Bad','lot':'BAD','test_code':'CBC','instrument':'A','quantity':-1,'full_stock':10,'expiry':'2027-01-01','reason':'Test'})
        self.assertFalse(Lot.objects.filter(lot='BAD').exists())
    def test_staff_creation_requires_manager_and_first_change(self):
        data={'username':'newstaff','email':'new@example.invalid','role':'collector','temporary_password':'Good-test-password-123'}
        self.sign('cashier');self.assertEqual(self.client.post('/accounts/',data).status_code,403)
        self.sign('manager');self.assertEqual(self.client.post('/accounts/',data).status_code,302)
        self.assertTrue(Account.objects.get(user__username='newstaff').must_change_password)

    def test_password_change_rejects_reuse_and_clears_first_login_gate(self):
        user = self.user('collector')
        Account.objects.filter(user=user).update(must_change_password=True)
        self.sign('collector')
        self.client.post('/password/', {'old_password':'Test-only-strong-pass', 'new_password1':'Test-only-strong-pass', 'new_password2':'Test-only-strong-pass'})
        self.assertTrue(Account.objects.get(user=user).must_change_password)
        self.assertRedirects(self.client.post('/password/', {'old_password':'Test-only-strong-pass', 'new_password1':'Changed-test-password-123', 'new_password2':'Changed-test-password-123'}), '/')
        self.assertFalse(Account.objects.get(user=user).must_change_password)
        user.refresh_from_db()
        self.assertTrue(user.check_password('Changed-test-password-123'))
        self.assertEqual(self.client.get('/patients/').status_code, 200)

    def test_complete_patient_and_order_entry(self):
        self.sign('cashier')
        response = self.client.post('/patients/new/', {'name':'Second fictional patient','dob':'1992-03-02','gender':'Not specified','address':'Example address','phone':'555-0108','email':'second@example.invalid','insurance_provider':'Example insurer','policy_number':'P2','coverage':'Example coverage'})
        patient = Patient.objects.get(email='second@example.invalid')
        self.assertRedirects(response, f'/patients/{patient.pk}/')
        for route in ['walk-in', 'telephone']:
            response = self.client.post('/orders/new/', {'patient':patient.pk,'route':route,'physician_id':'DR2','physician_name':'Fictional physician','physician_contact':'doctor@example.invalid','insurance_provider':'Example insurer','policy_number':'P2','coverage':'Example coverage','test_code':'CBC','test_name':'Complete blood count','sample_type':'blood','units':'10^9/L','reference_range':'4–11'})
            order = Order.objects.filter(patient=patient, route=route).get()
            self.assertRedirects(response, f'/orders/{order.pk}/')
            self.assertEqual(order.result_status, 'pending')
            self.assertEqual(order.policy_number, 'P2')
            self.assertTrue(Event.objects.filter(record=f'Order {order.pk}', action='Test order entered').exists())
        self.assertContains(self.client.get(f'/patients/{patient.pk}/'), 'Complete blood count', count=2)

    def test_archived_patient_cannot_receive_new_orders(self):
        Patient.objects.filter(pk=self.patient.pk).update(active=False)
        self.sign('cashier')
        response = self.client.post('/orders/new/', {'patient':self.patient.pk,'route':'walk-in','physician_id':'DR2','physician_name':'Fictional physician','physician_contact':'doctor@example.invalid','insurance_provider':'Example insurer','policy_number':'P2','coverage':'Example coverage','test_code':'CBC','test_name':'Complete blood count','sample_type':'blood'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 1)

    def test_seed_repeatable_after_multiple_same_test_orders(self):
        with patch.dict('os.environ', {'CLMS_DEMO_PASSWORD':'Local-test-password-123'}):
            call_command('seed_demo', stdout=StringIO())
            patient = Patient.objects.get(email='alex@example.invalid')
            Order.objects.create(patient=patient, test_code='CBC', test_name='Another CBC')
            count = Order.objects.count()
            call_command('seed_demo', stdout=StringIO())
        self.assertEqual(Order.objects.count(), count)
        self.assertTrue(self.user('collector').check_password('Test-only-strong-pass'))
