from django import forms
from .models import Dokumen

class DokumenForm(forms.ModelForm):
    class Meta:
        model = Dokumen
        fields = ['judul', 'deskripsi','jenis', 'link_gdrive'] # Sesuaikan dengan field di models.py Anda
