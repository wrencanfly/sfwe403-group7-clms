from django.urls import path
from lab import views as v
urlpatterns=[
 path('',v.home,name='home'),path('login/',v.sign_in,name='login'),path('logout/',v.sign_out,name='logout'),path('password/',v.password,name='password'),
 path('accounts/',v.accounts,name='accounts'),path('accounts/<int:pk>/unlock/',v.unlock,name='unlock'),
 path('patients/',v.patients,name='patients'),path('patients/new/',v.patient_edit,name='patient_new'),path('patients/<int:pk>/',v.patient_detail,name='patient_detail'),path('patients/<int:pk>/edit/',v.patient_edit,name='patient_edit'),path('patients/<int:pk>/archive/',v.archive_patient,name='archive_patient'),
 path('inventory/',v.inventory,name='inventory'),path('inventory/new/',v.lot_edit,name='lot_new'),path('inventory/<int:pk>/edit/',v.lot_edit,name='lot_edit'),
 path('orders/',v.orders,name='orders'),path('orders/new/',v.order_new,name='order_new'),path('orders/<int:pk>/',v.order_detail,name='order_detail'),path('orders/<int:pk>/collect/',v.collection,name='collection'),path('samples/<int:pk>/label/',v.label,name='label'),path('profile/',v.profile,name='profile')]
