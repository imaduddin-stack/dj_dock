from django.urls import path
from . import views

app_name = 'dokumen'

urlpatterns = [
    path('', views.beranda, name='beranda'),
    path('add/', views.add_dokumen, name='add_dokumen'),
    path('list/', views.list_dokumen, name='list_dokumen'),
    path('led/', views.dokumen_led, name='dokumen_led'),
    path('lkps/', views.dokumen_lkps, name='dokumen_lkps'),
    path('lkps/daftar/', views.dokumen_lkps_by_tabel, name='dokumen_lkps_by_tabel'),
]