#!/usr/bin/env python
"""
Script untuk verifikasi integritas data LKPS/LED di database.
Mendeteksi issues seperti orphan records, mismatches, dll.

Usage:
    python verify_lkps_data.py
"""

import os
import sys
import django
from pathlib import Path
from collections import defaultdict

# Setup Django
PROJECT_ROOT = Path(__file__).resolve().parent
DJANGO_ROOT = PROJECT_ROOT / 'pste'
sys.path.insert(0, str(DJANGO_ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pste.settings')
django.setup()

from dokumen.models import Kriteria, LedKomponen, LkpsElemen, Dokumen
from django.db.models import Count, Q


def print_section(title):
    """Print formatted section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def verify_kriteria():
    """Verify Kriteria data."""
    print_section("1. VERIFIKASI KRITERIA")

    kriteria_count = Kriteria.objects.count()
    print(f"📊 Total Kriteria: {kriteria_count}")

    if kriteria_count == 0:
        print("❌ CRITICAL: Tidak ada Kriteria di database!")
        return False

    # Check for duplicates
    duplicates = Kriteria.objects.values('nomor').annotate(
        count=Count('id')
    ).filter(count__gt=1)

    if duplicates.exists():
        print(f"⚠️  DUPLIKAT DITEMUKAN ({duplicates.count()}):")
        for dup in duplicates:
            docs = Kriteria.objects.filter(nomor=dup['nomor'])
            print(f"   - Nomor '{dup['nomor']}' ada {dup['count']}x")
            for k in docs:
                print(f"     * ID {k.id}: {k.nama}")
    else:
        print("✅ Tidak ada duplikat Kriteria")

    # List all kriteria
    print("\n📋 Daftar Kriteria:")
    for k in Kriteria.objects.all().order_by('nomor'):
        led_count = LedKomponen.objects.filter(kriteria=k).count()
        lkps_count = LkpsElemen.objects.filter(kriteria=k).count()
        print(f"   {k.nomor:>4} | {k.nama[:40]:<40} | LED:{led_count:>2} | LKPS:{lkps_count:>2}")

    return True


def verify_led_komponen():
    """Verify LED Komponen data."""
    print_section("2. VERIFIKASI LED KOMPONEN")

    led_count = LedKomponen.objects.count()
    print(f"📊 Total LED Komponen: {led_count}")

    if led_count == 0:
        print("⚠️  WARNING: Tidak ada LED Komponen di database")
        return False

    # Check orphan records
    orphans = LedKomponen.objects.filter(kriteria__isnull=True)
    if orphans.exists():
        print(f"❌ ORPHAN RECORDS DITEMUKAN ({orphans.count()}):")
        for led in orphans:
            print(f"   - ID {led.id}: {led.kode} (NO KRITERIA)")
    else:
        print("✅ Tidak ada orphan LED Komponen")

    # Check for duplicates
    duplicates = LedKomponen.objects.values('kode').annotate(
        count=Count('id')
    ).filter(count__gt=1)

    if duplicates.exists():
        print(f"⚠️  DUPLIKAT DITEMUKAN ({duplicates.count()}):")
        for dup in duplicates:
            leds = LedKomponen.objects.filter(kode=dup['kode'])
            print(f"   - Kode '{dup['kode']}' ada {dup['count']}x")
    else:
        print("✅ Tidak ada duplikat LED Kode")

    # Statistics
    print("\n📊 Statistik LED per Kriteria:")
    for k in Kriteria.objects.all().order_by('nomor'):
        leds = LedKomponen.objects.filter(kriteria=k)
        if leds.exists():
            print(f"   {k.nomor}: {leds.count()} komponen")

    return True


def verify_lkps_elemen():
    """Verify LKPS Elemen data."""
    print_section("3. VERIFIKASI LKPS ELEMEN")

    lkps_count = LkpsElemen.objects.count()
    print(f"📊 Total LKPS Elemen: {lkps_count}")

    if lkps_count == 0:
        print("⚠️  WARNING: Tidak ada LKPS Elemen di database")
        return False

    # Check orphan records
    orphans = LkpsElemen.objects.filter(kriteria__isnull=True)
    if orphans.exists():
        print(f"❌ ORPHAN RECORDS DITEMUKAN ({orphans.count()}):")
        for lkps in orphans:
            print(f"   - ID {lkps.id}: {lkps.tabel_referensi} (NO KRITERIA)")
    else:
        print("✅ Tidak ada orphan LKPS Elemen")

    # Check for duplicates
    duplicates = LkpsElemen.objects.values('tabel_referensi').annotate(
        count=Count('id')
    ).filter(count__gt=1)

    if duplicates.exists():
        print(f"⚠️  DUPLIKAT DITEMUKAN ({duplicates.count()}):")
        for dup in duplicates:
            lkps_list = LkpsElemen.objects.filter(tabel_referensi=dup['tabel_referensi'])
            print(f"   - Tabel '{dup['tabel_referensi']}' ada {dup['count']}x")
    else:
        print("✅ Tidak ada duplikat LKPS Tabel Referensi")

    # Statistics
    print("\n📊 Statistik LKPS per Kriteria:")
    for k in Kriteria.objects.all().order_by('nomor'):
        lkps_list = LkpsElemen.objects.filter(kriteria=k)
        if lkps_list.exists():
            print(f"   {k.nomor}: {lkps_list.count()} elemen")

    return True


def verify_dokumen_relations():
    """Verify Dokumen relations to LED and LKPS."""
    print_section("4. VERIFIKASI RELASI DOKUMEN-LED-LKPS")

    dok_total = Dokumen.objects.count()
    dok_dengan_led = Dokumen.objects.filter(dipakai_led__isnull=False).distinct().count()
    dok_dengan_lkps = Dokumen.objects.filter(dipakai_lkps__isnull=False).distinct().count()
    dok_dengan_keduanya = Dokumen.objects.filter(
        dipakai_lkps__isnull=False,
        dipakai_led__isnull=False
    ).distinct().count()

    print(f"📊 Total Dokumen: {dok_total}")
    print(f"   - Dengan LED: {dok_dengan_led} ({dok_dengan_led*100//dok_total if dok_total else 0}%)")
    print(f"   - Dengan LKPS: {dok_dengan_lkps} ({dok_dengan_lkps*100//dok_total if dok_total else 0}%)")
    print(f"   - Dengan keduanya: {dok_dengan_keduanya}")
    print(f"   - Tanpa relasi: {dok_total - max(dok_dengan_led, dok_dengan_lkps)}")

    # Detailed analysis
    print("\n📋 Dokumen dengan LKPS:")
    dokumen_lkps = Dokumen.objects.filter(dipakai_lkps__isnull=False).distinct()
    if dokumen_lkps.exists():
        for dok in dokumen_lkps[:10]:  # Show first 10
            lkps_count = dok.dipakai_lkps.count()
            lkps_list = ", ".join([l.tabel_referensi for l in dok.dipakai_lkps.all()])
            print(f"   - {dok.judul[:40]:<40} → {lkps_count} LKPS")
            print(f"     {lkps_list}")
        if dokumen_lkps.count() > 10:
            print(f"   ... dan {dokumen_lkps.count() - 10} dokumen lainnya")
    else:
        print("   (Tidak ada dokumen dengan LKPS)")

    print("\n📋 Dokumen dengan LED:")
    dokumen_led = Dokumen.objects.filter(dipakai_led__isnull=False).distinct()
    if dokumen_led.exists():
        for dok in dokumen_led[:10]:  # Show first 10
            led_count = dok.dipakai_led.count()
            led_list = ", ".join([l.kode for l in dok.dipakai_led.all()])
            print(f"   - {dok.judul[:40]:<40} → {led_count} LED")
            print(f"     {led_list}")
        if dokumen_led.count() > 10:
            print(f"   ... dan {dokumen_led.count() - 10} dokumen lainnya")
    else:
        print("   (Tidak ada dokumen dengan LED)")

    return True


def verify_lkps_usage():
    """Verify LKPS element usage statistics."""
    print_section("5. STATISTIK PENGGUNAAN LKPS")

    # LKPS with usage
    lkps_with_usage = LkpsElemen.objects.annotate(
        dokumen_count=Count('dokumen_terkait')
    ).filter(dokumen_count__gt=0).order_by('-dokumen_count')

    print(f"📊 Total LKPS yang digunakan: {lkps_with_usage.count()}")
    print("\n📋 Top 10 LKPS paling banyak digunakan:")

    for i, lkps in enumerate(lkps_with_usage[:10], 1):
        print(f"   {i:>2}. {lkps.tabel_referensi:<15} ({lkps.kriteria.nomor:<4}) → {lkps.dokumen_count} dokumen")

    # LKPS without usage
    lkps_unused = LkpsElemen.objects.annotate(
        dokumen_count=Count('dokumen_terkait')
    ).filter(dokumen_count=0)

    if lkps_unused.exists():
        print(f"\n⚠️  LKPS yang tidak digunakan: {lkps_unused.count()}")
        for lkps in lkps_unused[:5]:
            print(f"   - {lkps.tabel_referensi} ({lkps.kriteria.nomor})")
        if lkps_unused.count() > 5:
            print(f"   ... dan {lkps_unused.count() - 5} lainnya")

    return True


def verify_led_usage():
    """Verify LED component usage statistics."""
    print_section("6. STATISTIK PENGGUNAAN LED")

    # LED with usage
    led_with_usage = LedKomponen.objects.annotate(
        dokumen_count=Count('dokumen_terkait')
    ).filter(dokumen_count__gt=0).order_by('-dokumen_count')

    print(f"📊 Total LED yang digunakan: {led_with_usage.count()}")
    print("\n📋 Top 10 LED paling banyak digunakan:")

    for i, led in enumerate(led_with_usage[:10], 1):
        print(f"   {i:>2}. {led.kode:<15} ({led.kriteria.nomor:<4}) → {led.dokumen_count} dokumen")

    # LED without usage
    led_unused = LedKomponen.objects.annotate(
        dokumen_count=Count('dokumen_terkait')
    ).filter(dokumen_count=0)

    if led_unused.exists():
        print(f"\n⚠️  LED yang tidak digunakan: {led_unused.count()}")
        for led in led_unused[:5]:
            print(f"   - {led.kode} ({led.kriteria.nomor})")
        if led_unused.count() > 5:
            print(f"   ... dan {led_unused.count() - 5} lainnya")

    return True


def main():
    """Run all verifications."""
    print("\n" + "="*70)
    print("  VERIFIKASI INTEGRITAS DATA LKPS/LED DJ-DOCK")
    print("="*70)

    results = []

    try:
        results.append(("Kriteria", verify_kriteria()))
        results.append(("LED Komponen", verify_led_komponen()))
        results.append(("LKPS Elemen", verify_lkps_elemen()))
        results.append(("Relasi Dokumen", verify_dokumen_relations()))
        results.append(("Penggunaan LKPS", verify_lkps_usage()))
        results.append(("Penggunaan LED", verify_led_usage()))
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return

    # Summary
    print_section("RINGKASAN VERIFIKASI")

    print("Status Verifikasi:")
    for name, status in results:
        status_str = "✅ OK" if status else "⚠️  PERLU PERHATIAN"
        print(f"  {status_str} - {name}")

    all_ok = all(status for _, status in results)

    print("\n" + "="*70)
    if all_ok:
        print("✅ SEMUA VERIFIKASI PASSED - Data integrity OK")
    else:
        print("⚠️  ADA ISSUES YANG PERLU DITANGANI - Check output di atas")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
