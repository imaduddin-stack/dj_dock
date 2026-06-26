from django.db import models

# --- MODEL UNTUK LED ---
class Kriteria(models.Model):
    nomor = models.CharField(max_length=10, help_text="Contoh: K1, K2")
    nama = models.CharField(max_length=255, help_text="Contoh: Visi, Misi, Tujuan, dan Strategi")

    def __str__(self):
        return f"{self.nomor} - {self.nama}"

    class Meta:
        verbose_name_plural = "LED - Kriteria"

class LedKomponen(models.Model):
    kriteria = models.ForeignKey(Kriteria, on_delete=models.CASCADE, related_name='komponen')
    kode = models.CharField(max_length=20, help_text="Contoh: C.1.4")
    deskripsi = models.TextField()

    def __str__(self):
        return f"{self.kriteria.nomor} | {self.kode}"

    class Meta:
        verbose_name_plural = "LED - Komponen"


# --- MODEL UNTUK LKPS ---

class LkpsElemen(models.Model):
    kriteria = models.ForeignKey(Kriteria, on_delete=models.CASCADE, related_name='elemen')
    tabel_referensi = models.CharField(max_length=50, help_text="Contoh: Tabel 2.a, Tabel 3.a.1")
    deskripsi = models.TextField()

    def __str__(self):
        return f"{self.kriteria.nomor} | {self.tabel_referensi}"

    class Meta:
        verbose_name_plural = "LKPS - Tabel"


# --- MODEL DOKUMEN UTAMA ---
class Dokumen(models.Model):
    JENIS_DOKUMEN = [
        ('kebijakan', 'Kebijakan'),
        ('bukti_kegiatan', 'Bukti Kegiatan'),
        ('sk', 'Surat Keputusan'),
        ('laporan', 'Laporan'),
        ('instrumen', 'Instrumen'),
        ('monev', 'Monev'),
        ('lainnya', 'Lainnya'),
    ]

    judul = models.CharField(max_length=255)
    jenis = models.CharField(max_length=30, choices=JENIS_DOKUMEN)
    deskripsi = models.TextField()
    link_gdrive = models.URLField(max_length=500, help_text="Masukkan URL Google Drive dokumen")

    # Relasi Many-to-Many ke LedKomponen
    dipakai_led = models.ManyToManyField(LedKomponen, blank=True, related_name='dokumen_led_terkait')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.get_jenis_display()}] {self.judul}"

    class Meta:
        verbose_name_plural = "Arsip Dokumen"
        ordering = ['-created_at']


class DokumenLkps(models.Model):
    dokumen = models.ForeignKey(Dokumen, on_delete=models.CASCADE, related_name='lkps_elemen')
    lkps_elemen = models.ForeignKey(LkpsElemen, on_delete=models.CASCADE, related_name='dokumen_terkait')
    keterangan = models.CharField(max_length=255, blank=True, help_text="Catatan tambahan relasi")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.dokumen.judul} → {self.lkps_elemen.tabel_referensi}"

    class Meta:
        verbose_name_plural = "Dokumen - LKPS Tabel"
        unique_together = ('dokumen', 'lkps_elemen')
        ordering = ['dokumen', 'lkps_elemen']