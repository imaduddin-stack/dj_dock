#!/usr/bin/env python
"""
Script untuk seed data dari Excel ke database Django.
File Excel harus memiliki sheets: 'Kriteria', 'LedKomponen', 'LkpsElemen', 'Dokumen'

Usage:
    python seed_data.py
"""

import os
import sys
import django
from pathlib import Path

# Setup Django - script harus dijalankan dari direktori dj_dock/
PROJECT_ROOT = Path(__file__).resolve().parent  # d:\MYDATA\Project\dj_dock\
DJANGO_ROOT = PROJECT_ROOT / 'pste'  # d:\MYDATA\Project\dj_dock\pste\

# Validasi struktur
if not DJANGO_ROOT.exists():
    print(f"❌ Error: Direktori Django tidak ditemukan di {DJANGO_ROOT}")
    print(f"   Script harus dijalankan dari: {PROJECT_ROOT}")
    sys.exit(1)

sys.path.insert(0, str(DJANGO_ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pste.settings')
django.setup()

import openpyxl
from openpyxl import load_workbook
from dokumen.models import Kriteria, LedKomponen, LkpsElemen, Dokumen


def read_excel_sheet(filename, sheet_name):
    """Baca sheet dari Excel file dan return sebagai list of dicts."""
    try:
        wb = load_workbook(str(filename))
        ws = wb[sheet_name]
    except KeyError:
        print(f"❌ Sheet '{sheet_name}' tidak ditemukan")
        return []
    except FileNotFoundError:
        print(f"❌ File {filename} tidak ditemukan")
        return []

    data = []
    headers = None

    for idx, row in enumerate(ws.iter_rows(values_only=True), 1):
        if idx == 1:  # Header row
            headers = [h.strip() if h else None for h in row]
            continue

        if not any(row):  # Skip empty rows
            continue

        row_data = {headers[i]: row[i] for i in range(len(headers)) if i < len(row)}
        data.append(row_data)

    return data


def seed_kriteria(data):
    """Seed data Kriteria dari Excel."""
    print("\n📋 Seeding Kriteria...")
    created_count = 0
    updated_count = 0

    for row in data:
        nomor = row.get('nomor', '').strip()
        nama = row.get('nama', '').strip()

        if not nomor or not nama:
            print(f"⚠️  Baris tidak lengkap: {row}")
            continue

        obj, created = Kriteria.objects.update_or_create(
            nomor=nomor,
            defaults={'nama': nama}
        )

        if created:
            created_count += 1
            print(f"  ✅ Dibuat: {obj}")
        else:
            updated_count += 1
            print(f"  🔄 Diupdate: {obj}")

    print(f"✔️  Kriteria: {created_count} dibuat, {updated_count} diupdate")
    return created_count + updated_count


def seed_led_komponen(data):
    """Seed data LedKomponen dari Excel."""
    print("\n📋 Seeding LED Komponen...")
    created_count = 0
    updated_count = 0

    for row in data:
        nomor_kriteria = row.get('kriteria', '').strip()
        kode = row.get('kode', '').strip()
        deskripsi = row.get('deskripsi', '').strip()

        if not nomor_kriteria or not kode or not deskripsi:
            print(f"⚠️  Baris tidak lengkap: {row}")
            continue

        try:
            kriteria = Kriteria.objects.get(nomor=nomor_kriteria)
        except Kriteria.DoesNotExist:
            print(f"❌ Kriteria '{nomor_kriteria}' tidak ditemukan")
            continue

        obj, created = LedKomponen.objects.update_or_create(
            kriteria=kriteria,
            kode=kode,
            defaults={'deskripsi': deskripsi}
        )

        if created:
            created_count += 1
            print(f"  ✅ Dibuat: {obj}")
        else:
            updated_count += 1
            print(f"  🔄 Diupdate: {obj}")

    print(f"✔️  LED Komponen: {created_count} dibuat, {updated_count} diupdate")
    return created_count + updated_count


def seed_lkps_elemen(data):
    """Seed data LkpsElemen dari Excel."""
    print("\n📋 Seeding LKPS Elemen...")
    created_count = 0
    updated_count = 0

    for row in data:
        nomor_kriteria = row.get('kriteria', '').strip()
        tabel_referensi = row.get('tabel_referensi', '').strip()
        deskripsi = row.get('deskripsi', '').strip()

        if not nomor_kriteria or not tabel_referensi or not deskripsi:
            print(f"⚠️  Baris tidak lengkap: {row}")
            continue

        try:
            kriteria = Kriteria.objects.get(nomor=nomor_kriteria)
        except Kriteria.DoesNotExist:
            print(f"❌ Kriteria '{nomor_kriteria}' tidak ditemukan")
            continue

        obj, created = LkpsElemen.objects.update_or_create(
            kriteria=kriteria,
            tabel_referensi=tabel_referensi,
            defaults={'deskripsi': deskripsi}
        )

        if created:
            created_count += 1
            print(f"  ✅ Dibuat: {obj}")
        else:
            updated_count += 1
            print(f"  🔄 Diupdate: {obj}")

    print(f"✔️  LKPS Elemen: {created_count} dibuat, {updated_count} diupdate")
    return created_count + updated_count


def seed_dokumen(data):
    """Seed data Dokumen dari Excel."""
    print("\n📋 Seeding Dokumen...")
    created_count = 0
    updated_count = 0

    for row in data:
        judul = row.get('judul', '').strip()
        jenis = row.get('jenis', '').strip()
        deskripsi = row.get('deskripsi', '').strip()
        link_gdrive = row.get('link_gdrive', '').strip()
        led_komponen_kodes = row.get('led_komponen', '')  # Format: "K1.1;K1.2;K2.1"
        lkps_elemen_tabel = row.get('lkps_elemen', '')    # Format: "Tabel 2.a;Tabel 3.a.1"

        if not judul or not jenis or not deskripsi or not link_gdrive:
            print(f"⚠️  Baris tidak lengkap: {row}")
            continue

        obj, created = Dokumen.objects.update_or_create(
            judul=judul,
            defaults={
                'jenis': jenis,
                'deskripsi': deskripsi,
                'link_gdrive': link_gdrive,
            }
        )

        # Handle Many-to-Many relationships
        if led_komponen_kodes:
            led_kodes = [k.strip() for k in str(led_komponen_kodes).split(';') if k.strip()]
            led_components = LedKomponen.objects.filter(kode__in=led_kodes)
            obj.dipakai_led.set(led_components)

        if lkps_elemen_tabel:
            tabel_refs = [t.strip() for t in str(lkps_elemen_tabel).split(';') if t.strip()]
            lkps_elements = LkpsElemen.objects.filter(tabel_referensi__in=tabel_refs)
            obj.dipakai_lkps.set(lkps_elements)

        if created:
            created_count += 1
            print(f"  ✅ Dibuat: {obj}")
        else:
            updated_count += 1
            print(f"  🔄 Diupdate: {obj}")

    print(f"✔️  Dokumen: {created_count} dibuat, {updated_count} diupdate")
    return created_count + updated_count


def main():
    """Main function."""
    excel_file = PROJECT_ROOT / 'seed_template.xlsx'

    if not excel_file.exists():
        print(f"❌ File tidak ditemukan: {excel_file}")
        sys.exit(1)

    print(f"📂 Membaca file: {excel_file}")
    print("=" * 60)

    total_seeded = 0

    # Seed Kriteria
    kriteria_data = read_excel_sheet(str(excel_file), 'Kriteria')
    if kriteria_data:
        total_seeded += seed_kriteria(kriteria_data)

    # Seed LED Komponen
    led_data = read_excel_sheet(str(excel_file), 'LedKomponen')
    if led_data:
        total_seeded += seed_led_komponen(led_data)

    # Seed LKPS Elemen
    lkps_data = read_excel_sheet(str(excel_file), 'LkpsElemen')
    if lkps_data:
        total_seeded += seed_lkps_elemen(lkps_data)

    # Seed Dokumen
    dokumen_data = read_excel_sheet(str(excel_file), 'Dokumen')
    if dokumen_data:
        total_seeded += seed_dokumen(dokumen_data)

    print("\n" + "=" * 60)
    print(f"✨ Seeding selesai! Total: {total_seeded} record")


if __name__ == '__main__':
    main()
