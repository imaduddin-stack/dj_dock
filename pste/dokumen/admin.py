from django.contrib import admin
from .models import Kriteria, LedKomponen, LkpsElemen, Dokumen, DokumenLkps

@admin.register(Kriteria)
class LedKriteriaAdmin(admin.ModelAdmin):
    list_display = ('nomor', 'nama')

@admin.register(LedKomponen)
class LedKomponenAdmin(admin.ModelAdmin):
    list_display = ('kode', 'kriteria', 'deskripsi')
    list_filter = ('kriteria',)


@admin.register(LkpsElemen)
class LkpsElemenAdmin(admin.ModelAdmin):
    list_display = ('tabel_referensi', 'kriteria', 'deskripsi')
    list_filter = ('kriteria',)

class DokumenLkpsInline(admin.TabularInline):
    model = DokumenLkps
    extra = 1
    fields = ('lkps_elemen', 'keterangan')
    raw_id_fields = ('lkps_elemen',)


@admin.register(Dokumen)
class DokumenAdmin(admin.ModelAdmin):
    list_display = ('judul', 'jenis', 'link_gdrive', 'created_at')
    list_filter = ('jenis',)
    search_fields = ('judul', 'deskripsi')

    filter_horizontal = ('dipakai_led',)
    inlines = [DokumenLkpsInline]

    fieldsets = (
        ('Informasi Utama', {
            'fields': ('judul', 'jenis', 'deskripsi', 'link_gdrive')
        }),
        ('Pemetaan Akreditasi', {
            'fields': ('dipakai_led',),
            'description': 'Pilih komponen LED yang didukung oleh dokumen ini. Elemen LKPS dapat ditambahkan di bawah.'
        }),
    )


@admin.register(DokumenLkps)
class DokumenLkpsAdmin(admin.ModelAdmin):
    list_display = ('dokumen', 'lkps_elemen', 'keterangan', 'created_at')
    list_filter = ('lkps_elemen__kriteria', 'created_at')
    search_fields = ('dokumen__judul', 'lkps_elemen__tabel_referensi')
    raw_id_fields = ('dokumen', 'lkps_elemen')
    readonly_fields = ('created_at',)