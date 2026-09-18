# 9Router Auto-Add (Atria) — Made by Rofi Indistira

Bot otomatis untuk **membuat API key Atria-asi.ai** lewat login Google (GSuite), lalu **menambahkan + mengetes semuanya** sebagai connection ke dashboard **9Router Proxy** (localhost:20128), siap pakai.

## Fitur

- Login Google OAuth otomatis (handle TOS Workspace & halaman consent, termasuk versi bahasa Indonesia)
- Buat API key `/api/keys` di Atria untuk tiap akun
- Simpan hasil sebagai `email;key` ke `api.txt` (anti-duplikat)
- Akun yang sukses dipindah ke `success_akun.txt`, yang gagal ke `failed_akun.txt`, dan otomatis dihapus dari `akun.txt`
- Inject key ke 9Router (`POST /api/providers`) dengan `defaultModel: Atria-Dawn-Preview`
- Auto-test semua connection setelah di-inject → status `active`, tanpa klik manual

## Struktur File

```
9router-auto/
├── astra_glogin.py     # step 1: login Google + buat API key Atria
├── inject_9router.py   # step 2: inject key ke 9Router + test
├── run.bat             # jalanin step 1 + step 2 sekali klik
├── run_step1.ps1       # wrapper PowerShell step 1
├── run_step2.ps1       # wrapper PowerShell step 2
├── akun.txt            # INPUT: akun GSuite (email:password), habis diproses auto-hapus
├── api.txt             # OUTPUT: hasil key (email;key) — auto-dipakai step 2
├── success_akun.txt    # OUTPUT: akun yang berhasil
├── failed_akun.txt     # OUTPUT: akun yang gagal
└── requirements.txt    # dependensi Python
```

## Persiapan

1. **Python 3.11+** terpasang, tambahkan ke `PATH`.
2. Install dependensi:

```cmd
pip install -r requirements.txt
```

3. 9Router Proxy kamu sudah jalan di `http://localhost:20128` dengan node Atria
   (`openai-compatible-responses-...`) yang `baseUrl`-nya `http://api.atria-asi.ai/v1`.
   Kalau node-nya beda ID, ubah `PROVIDER` di `inject_9router.py`.

## Cara Pakai

1. **Isi `akun.txt`** — satu akun GSuite per baris:

```
email1@domain.com:password1
email2@domain.com:password2
```

> Bisa pakai separator `:`, `;`, `|`, atau `,`. Baris `#` (komentar) diabaikan.

2. **Double-click `run.bat`** (atau jalankan manual):

```cmd
python astra_glogin.py
python inject_9router.py
```

3. Selesai:
   - Key tersimpan dibaris `email;key` di `api.txt`
   - Akun sukses → `success_akun.txt`, yang gagal → `failed_akun.txt`
   - `akun.txt` otomatis dikosongkan
   - Semua connection sudah masuk 9Router & berstatus `active`

## Catatan

- `api.txt` sekaligus berfungsi sebagai penanda anti-duplikat: akun yang sudah punya key
  akan di-skip di run berikutnya.
- Saat nambah akun baru, cukup tambahkan baris baru di `akun.txt` lalu jalankan `run.bat` lagi —
  akun lama tidak akan diproses ulang.
- Log lengkap tiap run tersimpan di `run.log`.
- Nama connection di 9Router memakai email akun, dan `defaultModel` selalu
  `Atria-Dawn-Preview` supaya tidak ada model "unknown".

## Disclaimer

Gunakan sesuai ketentuan layanan masing-masing (Google & Atria-asi.ai). Penulis tidak
bertanggung jawab atas penyalahgunaan dan akun yang terkena pembatasan.