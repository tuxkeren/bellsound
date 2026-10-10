# BellSound

Aplikasi bel otomatis berbasis desktop (Python + Tkinter) untuk **bell masuk**,
**istirahat**, **kopi break**, dan **pulang**. Suara bell dapat diganti dengan
file MP3, durasi pemutaran dapat dipilih (20 detik, 30 detik, 60 detik, atau
full file), jadwal bell diatur per jam dan hari, serta tersedia banyak **jenis
bell** (misalnya Normal, Ramadhan, Ujian, dst).

Aplikasi berjalan terus dan **tidak dapat ditutup tanpa password**. Tampilan
dibuat modern dan profesional, serta siap di-compile menjadi executable
menggunakan PyInstaller.

## Fitur

- **Kategori bell**: Bell Masuk, Bell Istirahat, Kopi Break, Bell Pulang, dan
  Lainnya (dengan warna berbeda).
- **Jenis bell (profil)**: kumpulan jadwal terpisah, misalnya `Normal`,
  `Ramadhan`, dan seterusnya. Ganti jenis bell aktif langsung dari topbar.
- **Jadwal fleksibel**: jam (HH:MM) dan pilihan hari (Senin sampai Minggu).
- **Sumber suara MP3**: pilih file `.mp3` (juga mendukung `.wav`, `.ogg`,
  `.flac`, `.m4a`) untuk tiap bell.
- **Durasi & loop**: putar 20/30/60 detik atau full file. File pendek dapat
  diulang (loop) hingga durasi tercapai.
- **Volume** global dan per-bell.
- **Keamanan**: password (PBKDF2-SHA256) untuk menutup aplikasi dan mengunci
  layar. Password default: `admin123` (segera ubah di menu Pengaturan).
- **Riwayat** bell yang pernah dibunyikan.
- **Autostart** saat komputer menyala (Windows, Linux, macOS).
- **Mode portable**: buat file kosong bernama `bellsound.portable` di samping
  executable untuk menyimpan data di folder aplikasi.

## Instalasi (dari source)

```bash
cd bellsound
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

> Untuk pemutaran suara, komputer perlu memiliki perangkat audio. Jika tidak
> ada perangkat audio, aplikasi tetap berjalan namun bell tidak berbunyi.

### Troubleshooting: audio tidak terdeteksi

Jika muncul keterangan **"Audio tidak tersedia"**, paling sering karena program
dijalankan dengan Python sistem yang tidak memiliki pygame, bukan karena
speaker bermasalah. Jalankan dengan venv proyek:

```bash
source .venv/bin/activate
python main.py
```

atau tanpa aktivasi: `.venv/bin/python main.py`. Sejak v1.0.1 program
langsung menolak dijalankan dan menampilkan pesan jelas jika dependensinya
belum terpasang pada interpreter yang dipakai.

## Compile menjadi executable

```bash
pip install -r requirements-dev.txt
python build.py            # satu file (onefile)
python build.py --onedir   # folder berisi executable
```

Hasil build ada di folder `dist/`. Pada Windows, hasilnya adalah
`dist/bellsound.exe`. Agar suara ikut terpaket, `build.py` sudah memakai
`--collect-all pygame`.

Opsional: letakkan ikon aplikasi di `assets/icon.ico` (Windows) atau
`assets/icon.png` (Linux/macOS) sebelum build agar ikut disertakan.

## Struktur proyek

```
bellsound/
├── main.py                  # titik masuk
├── build.py                 # skrip build PyInstaller
├── requirements.txt
├── requirements-dev.txt
└── bellsound/
    ├── app.py               # jendela utama, navigasi, kunci, close-guard
    ├── config.py            # konfigurasi JSON (profil, jadwal, setting)
    ├── models.py            # model BellEvent & Profile
    ├── player.py            # pemutaran audio (pygame)
    ├── scheduler.py         # penjadwalan bell
    ├── security.py          # hashing password
    ├── autostart.py         # autostart lintas platform
    ├── paths.py             # lokasi file data
    └── ui/
        ├── theme.py         # palet & font
        ├── widgets.py       # widget kustom (tombol, toggle, kartu, dll)
        ├── dialogs.py       # dialog password/konfirmasi/input
        ├── event_dialog.py  # form tambah/edit jadwal bell
        └── pages/           # dashboard, jadwal, jenis bell, riwayat, setting
```

## Lokasi data

- Windows: `%APPDATA%\bellsound`
- Linux: `~/.config/bellsound`
- macOS: `~/Library/Application Support/bellsound`
- Mode portable: `<folder aplikasi>/data`

## Catatan penggunaan

1. Buka menu **Jadwal Bell**, pilih **jenis bell**, lalu tambahkan bell dan
   pilih file MP3-nya.
2. Atur jam, hari, durasi, dan volume. Gunakan tombol **Putar** untuk menguji.
3. Biarkan aplikasi tetap berjalan. Bell akan berbunyi otomatis sesuai jadwal.
4. Untuk menutup aplikasi, klik tanda silang lalu masukkan password.

### Mode layar penuh

Aplikasi terbuka dalam **mode layar penuh** secara default. Tekan **Esc** untuk
beralih ke mode jendela, dan tekan **Esc** lagi untuk kembali ke layar penuh.

## Lisensi

Dirilis dengan lisensi **MIT** — lihat berkas [LICENSE](LICENSE).

