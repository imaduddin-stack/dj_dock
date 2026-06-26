from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .models import Dokumen, Kriteria, LkpsElemen, DokumenLkps
from .forms import DokumenForm
import json

def beranda(request):
    # Menghitung statistik dokumen untuk ditampilkan di dashboard
    total_dokumen = Dokumen.objects.count()
    jml_kebijakan = Dokumen.objects.filter(jenis='kebijakan').count()
    jml_laporan = Dokumen.objects.filter(jenis='laporan').count()
    jml_bukti = Dokumen.objects.filter(jenis='bukti_kegiatan').count()

    # Data untuk pie chart (jenis dokumen)
    jenis_counts = Dokumen.objects.values('jenis').annotate(count=Count('id'))
    jenis_labels = []
    jenis_data = []
    jenis_colors = {
        'kebijakan': '#0d6efd',
        'laporan': '#ffc107',
        'bukti_kegiatan': '#198754',
        'sk': '#dc3545',
        'instrumen': '#6f42c1',
        'monev': '#20c997',
        'lainnya': '#6c757d',
    }

    for item in jenis_counts:
        jenis_labels.append(dict(Dokumen.JENIS_DOKUMEN).get(item['jenis'], item['jenis']))
        jenis_data.append(item['count'])

    # Data untuk bar chart (dokumen per kriteria)
    kriteria_list = Kriteria.objects.all().order_by('nomor')
    kriteria_labels = []
    kriteria_data = []

    for kriteria in kriteria_list:
        # Hitung dokumen unik yang terkait dengan kriteria ini (via LED atau LKPS)
        dokumen_led = Dokumen.objects.filter(dipakai_led__kriteria=kriteria).distinct().count()
        dokumen_lkps = Dokumen.objects.filter(lkps_elemen__lkps_elemen__kriteria=kriteria).distinct().count()
        total_for_kriteria = len(set(list(Dokumen.objects.filter(dipakai_led__kriteria=kriteria).values_list('id', flat=True)) +
                                      list(Dokumen.objects.filter(lkps_elemen__lkps_elemen__kriteria=kriteria).values_list('id', flat=True))))

        if total_for_kriteria > 0 or True:  # Show all criteria even if empty
            kriteria_labels.append(kriteria.nomor)
            kriteria_data.append(total_for_kriteria)

    # Data untuk highlight: Top 10 Tabel LKPS dengan dokumen paling sedikit
    tabel_lkps_dengan_dokumentasi = []
    tabel_refs = LkpsElemen.objects.values('tabel_referensi').distinct()

    for tabel in tabel_refs:
        tabel_ref = tabel['tabel_referensi']
        jumlah_dokumen = DokumenLkps.objects.filter(
            lkps_elemen__tabel_referensi=tabel_ref
        ).values('dokumen').distinct().count()

        # Ambil deskripsi pertama untuk tabel ini
        sample_elemen = LkpsElemen.objects.filter(tabel_referensi=tabel_ref).first()

        tabel_lkps_dengan_dokumentasi.append({
            'tabel_referensi': tabel_ref,
            'jumlah': jumlah_dokumen,
            'deskripsi': sample_elemen.deskripsi if sample_elemen else '',
        })

    # Pisahkan item dengan 0 dokumen dan non-zero, lalu urutkan
    items_with_zero = [x for x in tabel_lkps_dengan_dokumentasi if x['jumlah'] == 0]
    items_with_nonzero = sorted([x for x in tabel_lkps_dengan_dokumentasi if x['jumlah'] > 0], key=lambda x: x['jumlah'])

    # Ambil items dengan 0 (semua), plus sisa top items untuk total max 10
    remaining_slots = max(0, 10 - len(items_with_zero))
    tabel_dengan_sedikit_dokumen = items_with_zero + items_with_nonzero[:remaining_slots]

    # Dokumen terbaru (10 dokumen)
    dokumen_terbaru = Dokumen.objects.all().order_by('-created_at')[:10]

    # Mengambil query pencarian
    query = request.GET.get('q', '')

    # Filter dokumen berdasarkan pencarian
    if query:
        dokumen_queryset = Dokumen.objects.filter(
            Q(judul__icontains=query) | Q(deskripsi__icontains=query)
        )
    else:
        dokumen_queryset = Dokumen.objects.all()

    # Pagination
    paginator = Paginator(dokumen_queryset, 15)
    page_number = request.GET.get('page')
    dokumen_list = paginator.get_page(page_number)

    context = {
        'total_dokumen': total_dokumen,
        'jml_kebijakan': jml_kebijakan,
        'jml_laporan': jml_laporan,
        'jml_bukti': jml_bukti,
        'dokumen_list': dokumen_list,
        'dokumen_terbaru': dokumen_terbaru,
        'query': query,
        'jenis_labels': json.dumps(jenis_labels),
        'jenis_data': json.dumps(jenis_data),
        'jenis_colors': json.dumps([jenis_colors.get(item['jenis'], '#6c757d') for item in jenis_counts]),
        'kriteria_labels': json.dumps(kriteria_labels),
        'kriteria_data': json.dumps(kriteria_data),
        'kriteria_dengan_sedikit_dokumen': tabel_dengan_sedikit_dokumen,
    }
    return render(request, 'dokumen/beranda.html', context)

def add_dokumen(request):
    if request.method == 'POST':
        form = DokumenForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('dokumen:beranda')
    else:
        form = DokumenForm()
    return render(request, 'dokumen/add.html', {'form': form})

def list_dokumen(request):
    dokumen_list = Dokumen.objects.all()
    return render(request, 'dokumen/list.html', {'dokumen_list': dokumen_list})

def dokumen_led(request):
    query = request.GET.get('q', '')

    # Ambil semua kriteria dengan komponennya
    kriteria_list = Kriteria.objects.prefetch_related('komponen').all()

    # Filter per kriteria
    kriteria_dengan_dokumen = []
    for kriteria in kriteria_list:
        komponens = kriteria.komponen.all()
        if query:
            komponens = komponens.filter(
                Q(deskripsi__icontains=query) |
                Q(dokumen_led_terkait__judul__icontains=query) |
                Q(dokumen_led_terkait__deskripsi__icontains=query)
            ).distinct()

        if komponens.exists():
            # Ambil dokumen unik per komponen
            dokumen_dict = {}
            for komponen in komponens:
                for dokumen in komponen.dokumen_led_terkait.all():
                    if dokumen.id not in dokumen_dict:
                        dokumen_dict[dokumen.id] = dokumen

            if dokumen_dict:
                kriteria_dengan_dokumen.append({
                    'kriteria': kriteria,
                    'komponens': komponens,
                    'dokumen': list(dokumen_dict.values())
                })

    context = {
        'kriteria_dengan_dokumen': kriteria_dengan_dokumen,
        'query': query,
        'title': 'Dokumen LED',
    }
    return render(request, 'dokumen/dokumen_led.html', context)

def dokumen_lkps_by_tabel(request):
    """View untuk menampilkan daftar dokumen berdasarkan kriteria dan tabel LKPS"""
    kriteria_id = request.GET.get('kriteria')
    tabel_referensi = request.GET.get('tabel')
    query = request.GET.get('q', '')

    kriteria_list = Kriteria.objects.all().order_by('nomor')
    selected_kriteria = None
    dokumen_list = []
    kebijakan_dokumen = []

    if kriteria_id and tabel_referensi:
        try:
            selected_kriteria = Kriteria.objects.get(id=kriteria_id)

            # Ambil dokumen berdasarkan kriteria dan tabel LKPS
            dokumen_query = DokumenLkps.objects.filter(
                lkps_elemen__kriteria=selected_kriteria,
                lkps_elemen__tabel_referensi=tabel_referensi
            ).select_related('dokumen').values_list('dokumen', flat=True).distinct()

            dokumen_list = Dokumen.objects.filter(id__in=dokumen_query)

            if query:
                dokumen_list = dokumen_list.filter(
                    Q(judul__icontains=query) | Q(deskripsi__icontains=query)
                )

            # Ambil dokumen kebijakan untuk panel terpisah
            kebijakan_dokumen = dokumen_list.filter(jenis='kebijakan')

        except Kriteria.DoesNotExist:
            pass

    # Pagination
    paginator = Paginator(dokumen_list, 15)
    page_number = request.GET.get('page')
    dokumen_page = paginator.get_page(page_number)

    context = {
        'kriteria_list': kriteria_list,
        'selected_kriteria': selected_kriteria,
        'tabel_referensi': tabel_referensi,
        'dokumen_list': dokumen_page,
        'kebijakan_dokumen': kebijakan_dokumen,
        'query': query,
        'title': f'Dokumen LKPS - {tabel_referensi}',
    }
    return render(request, 'dokumen/dokumen_lkps_daftar.html', context)


def dokumen_lkps(request):
    kriteria_id = request.GET.get('kriteria')

    # Ambil semua kriteria untuk dropdown
    kriteria_list = Kriteria.objects.all().order_by('nomor')

    # Jika kriteria dipilih, tampilkan tabel LKPS terkait
    tabel_lkps_list = []
    selected_kriteria = None

    if kriteria_id:
        try:
            selected_kriteria = Kriteria.objects.get(id=kriteria_id)

            # Ambil semua elemen LKPS untuk kriteria ini
            elemen_list = LkpsElemen.objects.filter(kriteria=selected_kriteria).values('tabel_referensi').distinct()

            # Untuk setiap tabel_referensi, hitung jumlah dokumen dan ambil info tabelnya
            for elemen in elemen_list:
                tabel_ref = elemen['tabel_referensi']

                # Ambil satu elemen sebagai sampel untuk deskripsi
                sample_elemen = LkpsElemen.objects.filter(
                    kriteria=selected_kriteria,
                    tabel_referensi=tabel_ref
                ).first()

                # Hitung jumlah dokumen unik untuk tabel ini
                jumlah_dokumen = DokumenLkps.objects.filter(
                    lkps_elemen__kriteria=selected_kriteria,
                    lkps_elemen__tabel_referensi=tabel_ref
                ).values('dokumen').distinct().count()

                tabel_lkps_list.append({
                    'tabel_referensi': tabel_ref,
                    'deskripsi': sample_elemen.deskripsi if sample_elemen else '',
                    'jumlah_dokumen': jumlah_dokumen,
                    'kriteria_id': kriteria_id,
                })
        except Kriteria.DoesNotExist:
            pass

    context = {
        'kriteria_list': kriteria_list,
        'selected_kriteria': selected_kriteria,
        'tabel_lkps_list': tabel_lkps_list,
        'title': 'Dokumen LKPS',
    }
    return render(request, 'dokumen/dokumen_lkps.html', context)     

