#!/usr/bin/env python
import os
import sys
import django
import openpyxl
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pste.settings')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pste'))
django.setup()

from dokumen.models import Dokumen, LkpsElemen, DokumenLkps

def import_dokumen_lkps_from_excel(excel_file):
    """Import relasi Dokumen-LKPS dari Excel sheet Dokumen"""
    wb = openpyxl.load_workbook(excel_file)
    ws = wb['Dokumen']

    success_count = 0
    skip_count = 0
    error_count = 0
    errors_log = []

    print(f"\nMembaca file: {excel_file}")
    print("=" * 70)

    # Iterate rows (skip header)
    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        try:
            dokumen_id = row[0]
            judul = row[1]
            lkps_str = row[6]  # Column 7 = dipakai_lkps

            # Skip jika dokumen_id tidak ada atau lkps_str kosong
            if not dokumen_id or not lkps_str:
                skip_count += 1
                continue

            # Cari dokumen
            try:
                dokumen = Dokumen.objects.get(id=dokumen_id)
            except Dokumen.DoesNotExist:
                error_count += 1
                errors_log.append(f"Row {row_idx}: Dokumen ID {dokumen_id} tidak ditemukan")
                continue

            # Parse LKPS (format: "Tabel 1.a;Tabel 1.b;Tabel 2.a")
            lkps_list = [l.strip() for l in str(lkps_str).split(';') if l.strip()]

            for lkps_ref in lkps_list:
                try:
                    # Cari LkpsElemen berdasarkan tabel_referensi
                    lkps_elemen = LkpsElemen.objects.get(tabel_referensi=lkps_ref)

                    # Create atau update DokumenLkps (unique_together constraint)
                    dok_lkps, created = DokumenLkps.objects.get_or_create(
                        dokumen=dokumen,
                        lkps_elemen=lkps_elemen,
                        defaults={'keterangan': ''}
                    )

                    if created:
                        success_count += 1
                        print(f"  ✓ Row {row_idx}: {judul} → {lkps_ref}")
                    else:
                        print(f"  ~ Row {row_idx}: {judul} → {lkps_ref} (sudah ada)")

                except LkpsElemen.DoesNotExist:
                    error_count += 1
                    errors_log.append(f"Row {row_idx}: LKPS Elemen '{lkps_ref}' tidak ditemukan")
                    continue

        except Exception as e:
            error_count += 1
            errors_log.append(f"Row {row_idx}: {str(e)}")
            continue

    # Print summary
    print("\n" + "=" * 70)
    print(f"\n[SUMMARY]")
    print(f"  Berhasil dibuat: {success_count}")
    print(f"  Sudah ada: {skip_count}")
    print(f"  Error: {error_count}")

    if errors_log:
        print(f"\n[ERROR LOG]")
        for error in errors_log[:10]:  # Show first 10 errors
            print(f"  - {error}")
        if len(errors_log) > 10:
            print(f"  ... dan {len(errors_log) - 10} error lainnya")

    return success_count, skip_count, error_count


def main():
    excel_file = "seed_template.xlsx"

    if not os.path.exists(excel_file):
        print(f"ERROR: File {excel_file} tidak ditemukan!")
        sys.exit(1)

    print(f"\n{'=' * 70}")
    print(f"Import Relasi Dokumen-LKPS dari Excel")
    print(f"File: {excel_file}")
    print(f"{'=' * 70}")

    success, skip, error = import_dokumen_lkps_from_excel(excel_file)

    print(f"\n{'=' * 70}")
    print(f"Total DokumenLkps yang dibuat: {success}")
    print(f"Total error: {error}")
    print(f"{'=' * 70}\n")


if __name__ == '__main__':
    main()
