#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pste.settings')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pste'))
django.setup()

from django.apps import apps
from dokumen.models import Kriteria, LedKomponen, LkpsElemen, Dokumen, DokumenLkps

def create_excel_sheet(wb, sheet_name, headers, data_rows, max_rows=None):
    """Helper untuk membuat sheet dengan style"""
    ws = wb.create_sheet(sheet_name)

    # Limit rows jika diperlukan
    if max_rows and len(data_rows) > max_rows:
        data_rows = data_rows[:max_rows]
        ws.append_rows_note = f"(Showing {max_rows} of {len(data_rows)} rows)"

    # Header style
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True, size=11)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # Write headers
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.border = border
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

    # Write data
    for row_num, row_data in enumerate(data_rows, 2):
        for col_num, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_num, column=col_num)

            # Handle None values
            if value is None:
                cell.value = ""
            elif isinstance(value, datetime):
                cell.value = value.strftime("%Y-%m-%d %H:%M:%S")
            else:
                cell.value = str(value)[:500]  # Limit text length

            cell.border = border
            cell.alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)

    # Auto adjust column width
    for col_num, header in enumerate(headers, 1):
        max_length = len(str(header))
        column = openpyxl.utils.get_column_letter(col_num)

        for row_num in range(2, min(len(data_rows) + 2, 100)):  # Sample first 100 rows for width
            cell = ws[f'{column}{row_num}']
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))

        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column].width = adjusted_width

    # Freeze header row
    ws.freeze_panes = 'A2'

    return ws, len(data_rows)

def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"database_dump_all_{timestamp}.xlsx"

    wb = openpyxl.Workbook()
    wb.remove(wb.active)  # Remove default sheet

    print(f"\n{'='*70}")
    print(f"DUMP ALL DATABASE")
    print(f"{'='*70}\n")

    total_records = 0

    # 1. KRITERIA
    print("Exporting Kriteria...")
    kriteria_list = Kriteria.objects.all()
    kriteria_data = [[k.id, k.nomor, k.nama] for k in kriteria_list]
    ws, count = create_excel_sheet(wb, "1_Kriteria", ["ID", "Nomor", "Nama"], kriteria_data)
    total_records += count
    print(f"  [OK] {count} records")

    # 2. LED KOMPONEN
    print("Exporting LED Komponen...")
    komponen_list = LedKomponen.objects.select_related('kriteria').all()
    komponen_data = [
        [k.id, k.kriteria.nomor, k.kriteria.nama, k.kode, k.deskripsi]
        for k in komponen_list
    ]
    ws, count = create_excel_sheet(wb, "2_LED_Komponen",
        ["ID", "Kriteria No", "Kriteria Nama", "Kode", "Deskripsi"], komponen_data)
    total_records += count
    print(f"  [OK] {count} records")

    # 3. LKPS ELEMEN
    print("Exporting LKPS Elemen...")
    elemen_list = LkpsElemen.objects.select_related('kriteria').all()
    elemen_data = [
        [e.id, e.kriteria.nomor, e.kriteria.nama, e.tabel_referensi, e.deskripsi]
        for e in elemen_list
    ]
    ws, count = create_excel_sheet(wb, "3_LKPS_Elemen",
        ["ID", "Kriteria No", "Kriteria Nama", "Tabel Ref", "Deskripsi"], elemen_data)
    total_records += count
    print(f"  [OK] {count} records")

    # 4. DOKUMEN
    print("Exporting Dokumen...")
    dokumen_list = Dokumen.objects.all()
    dokumen_data = [
        [
            d.id,
            d.judul[:100],
            d.get_jenis_display(),
            d.deskripsi[:100] if d.deskripsi else "",
            d.link_gdrive,
            d.dipakai_led.count(),
            d.lkps_elemen.count(),
            d.created_at.strftime("%Y-%m-%d %H:%M:%S") if d.created_at else "",
            d.updated_at.strftime("%Y-%m-%d %H:%M:%S") if d.updated_at else ""
        ]
        for d in dokumen_list
    ]
    ws, count = create_excel_sheet(wb, "4_Dokumen",
        ["ID", "Judul (100 char)", "Jenis", "Deskripsi (100 char)", "Link GDrive",
         "LED Count", "LKPS Count", "Created At", "Updated At"], dokumen_data)
    total_records += count
    print(f"  [OK] {count} records")

    # 5. DOKUMEN-LED (M2M detail)
    print("Exporting Dokumen-LED relations...")
    dokumen_led_data = []
    for d in Dokumen.objects.all():
        for led in d.dipakai_led.all():
            dokumen_led_data.append([
                d.id,
                d.judul[:80],
                led.id,
                led.kode,
                led.kriteria.nomor
            ])
    ws, count = create_excel_sheet(wb, "5_Dokumen_LED",
        ["Dokumen ID", "Dokumen Judul", "LED ID", "LED Kode", "Kriteria"], dokumen_led_data)
    total_records += count
    print(f"  [OK] {count} relations")

    # 6. DOKUMEN-LKPS (Intermediate model detail)
    print("Exporting Dokumen-LKPS relations...")
    dokumen_lkps_list = DokumenLkps.objects.select_related('dokumen', 'lkps_elemen', 'lkps_elemen__kriteria').all()
    dokumen_lkps_data = [
        [
            dl.id,
            dl.dokumen.id,
            dl.dokumen.judul[:80],
            dl.lkps_elemen.id,
            dl.lkps_elemen.tabel_referensi,
            dl.lkps_elemen.kriteria.nomor,
            dl.keterangan,
            dl.created_at.strftime("%Y-%m-%d %H:%M:%S") if dl.created_at else ""
        ]
        for dl in dokumen_lkps_list
    ]
    ws, count = create_excel_sheet(wb, "6_Dokumen_LKPS",
        ["ID", "Dokumen ID", "Dokumen Judul", "LKPS ID", "LKPS Tabel Ref", "Kriteria No", "Keterangan", "Created At"],
        dokumen_lkps_data)
    total_records += count
    print(f"  [OK] {count} relations")

    # 7. SUMMARY SHEET
    print("Creating summary sheet...")
    summary_data = [
        ["Table", "Record Count"],
        ["Kriteria", Kriteria.objects.count()],
        ["LED Komponen", LedKomponen.objects.count()],
        ["LKPS Elemen", LkpsElemen.objects.count()],
        ["Dokumen", Dokumen.objects.count()],
        ["Dokumen-LED Relations", sum(d.dipakai_led.count() for d in Dokumen.objects.all())],
        ["Dokumen-LKPS Relations", DokumenLkps.objects.count()],
        ["", ""],
        ["TOTAL RECORDS", total_records],
        ["Export Date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
    ]
    ws, _ = create_excel_sheet(wb, "0_SUMMARY", ["Deskripsi", "Jumlah"], summary_data)

    # Save file
    wb.save(output_file)

    print(f"\n{'='*70}")
    print(f"[OK] Database dump berhasil dibuat: {output_file}")
    print(f"{'='*70}\n")

    # Print summary
    print("SUMMARY:")
    print(f"  - Kriteria: {Kriteria.objects.count()} records")
    print(f"  - LED Komponen: {LedKomponen.objects.count()} records")
    print(f"  - LKPS Elemen: {LkpsElemen.objects.count()} records")
    print(f"  - Dokumen: {Dokumen.objects.count()} records")
    print(f"  - Dokumen-LED Relations: {sum(d.dipakai_led.count() for d in Dokumen.objects.all())} relations")
    print(f"  - Dokumen-LKPS Relations: {DokumenLkps.objects.count()} relations")
    print(f"\nTotal sheets: 7")
    print(f"File size: ~{os.path.getsize(output_file) / 1024:.1f} KB\n")

if __name__ == '__main__':
    main()
