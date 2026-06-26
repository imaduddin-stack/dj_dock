import csv
import os
from django.core.management.base import BaseCommand
from pste.dokumen.models import Dokumen

class Command(BaseCommand):
    help = 'Import dokumen dari file CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path ke file CSV'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']

        if not os.path.exists(csv_file):
            self.stdout.write(
                self.style.ERROR(f'File tidak ditemukan: {csv_file}')
            )
            return

        imported_count = 0
        skipped_count = 0

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';')
            next(reader)  # Skip header jika ada

            for row in reader:
                try:
                    # Parse struktur: Kategori;Sub1;Sub2;Sub3;Sub4;Sub5;File
                    kategori = row[0].strip() if row[0] else ''
                    sub_kategori = row[1].strip() if len(row) > 1 and row[1] else ''
                    sub_sub = row[2].strip() if len(row) > 2 and row[2] else ''

                    # Filename adalah kolom terakhir yang tidak kosong
                    filename = ''
                    for i in range(len(row) - 1, -1, -1):
                        if row[i].strip():
                            filename = row[i].strip()
                            break

                    # Skip jika tidak ada filename
                    if not filename or filename == kategori:
                        skipped_count += 1
                        continue

                    # Tentukan jenis dokumen
                    jenis = self.map_jenis(kategori)

                    # Buat judul dari struktur folder
                    judul = f"{sub_kategori} - {filename}" if sub_kategori else filename
                    judul = judul[:255]  # Batasi panjang

                    # Buat deskripsi dari struktur
                    deskripsi = f"Kategori: {kategori}"
                    if sub_kategori:
                        deskripsi += f" | Sub: {sub_kategori}"
                    if sub_sub:
                        deskripsi += f" | {sub_sub}"

                    # Cek apakah sudah ada
                    if Dokumen.objects.filter(judul=judul, jenis=jenis).exists():
                        skipped_count += 1
                        continue

                    # Buat dokumen
                    dokumen = Dokumen.objects.create(
                        judul=judul,
                        jenis=jenis,
                        deskripsi=deskripsi,
                        link_gdrive='https://drive.google.com/placeholder'  # Placeholder
                    )

                    imported_count += 1

                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'Error pada baris {row}: {str(e)}')
                    )
                    skipped_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'\nBerhasil mengimport {imported_count} dokumen\n'
                f'Skipped: {skipped_count} dokumen'
            )
        )

    def map_jenis(self, kategori):
        """Map kategori folder ke jenis dokumen"""
        kategori_lower = kategori.lower()

        if 'kebijakan' in kategori_lower:
            return 'kebijakan'
        elif 'laporan' in kategori_lower or 'lkps' in kategori_lower:
            return 'laporan'
        elif 'led' in kategori_lower:
            return 'bukti_kegiatan'
        elif 'instrumen' in kategori_lower:
            return 'instrumen'
        elif 'monev' in kategori_lower:
            return 'monev'
        else:
            return 'lainnya'
