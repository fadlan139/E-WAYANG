# E-Wayang: Program Wayang Kulit Digital Interaktif

**Bima dan Arjuna – Janji di Tengah Hutan**

E-Wayang adalah proyek interaktif berbasis computer vision yang menampilkan wayang kulit digital dengan tokoh Bima dan Arjuna. Aplikasi ini menggunakan MediaPipe hand tracking untuk mengendalikan karakter melalui gerakan tangan, sehingga pengguna dapat berinteraksi dengan cerita secara langsung.

---

## 1. Deskripsi Proyek

Proyek ini dibuat untuk melestarikan budaya wayang Indonesia dengan pendekatan modern. Pengguna dapat:

- Menggerakkan wayang menggunakan tangan
- Menikmati alur cerita interaktif Bima dan Arjuna
- Menonton narasi, dialog, dan musik yang sudah dibuat secara khusus
- Berpartisipasi dalam mode kuis dan pilihan karakter
- Menjalankan aplikasi dalam mode presentasi/proyektor

---

## 2. Fitur Utama

- Hand tracking menggunakan MediaPipe
- Mode cerita interaktif "Bima dan Arjuna – Janji di Tengah Hutan"
- Pilihan karakter wayang (Bima, Arjuna, Semar, Kapi Angeni, dll.)
- Sinkronisasi audio, subtitle, dan visual
- Mode fullscreen dan projector untuk presentasi
- Dapat dijalankan di Windows, macOS, dan Linux

---

## 3. Teknologi yang Digunakan

- Python 3.11+
- Pygame
- MediaPipe
- OpenCV
- NumPy

---

## 4. Struktur Folder

```text
E-WAYANG/
├── main.py
├── make_rig.py
├── preview_rig.py
├── rigmath.py
├── requirements.txt
├── environment.yml
├── config.json
├── story.json
├── README.md
├── SETUP.md
├── run.bat
├── run_debug.bat
├── run_projector.bat
├── assets/
├── audio/
├── .gitignore
├── *.png
├── *.jpg
├── *.mp3
└── *.json
```

---

## 5. Persyaratan Sistem

- Python 3.11 atau lebih baru
- Kamera webcam / built-in camera
- Minimal RAM 4 GB
- Speaker atau headphone
- Windows 10+, macOS, atau Linux

---

## 6. Cara Menjalankan

### 6.1 Install dependencies

```bash
pip install -r requirements.txt
```

### 6.2 Jalankan aplikasi

Windows:
```bash
run.bat
```

Mac/Linux:
```bash
python main.py
```

---

## 7. Kontrol Aplikasi

| Tombol | Fungsi |
|--------|--------|
| `SPACE` | Lanjut ke dialog atau adegan berikutnya |
| `F11` | Fullscreen |
| `P` | Mode projector |
| `ESC` | Keluar dari aplikasi |

---

## 8. Alur Cerita

1. Pembukaan
2. Jeda dan pengantar
3. Judul cerita
4. Adegan 1 sampai 5
5. Akhir cerita
6. Pesan moral
7. Penutup
8. Kuis penonton

---

## 9. Panduan Instalasi Detail

Untuk panduan setup langkah demi langkah, silakan lihat file:

- [SETUP.md](SETUP.md)

---

## 10. Catatan

Proyek ini dibuat sebagai bentuk inovasi digital untuk memperkenalkan wayang tradisional ke generasi muda dengan teknologi yang lebih modern. Fokus utama dari aplikasi ini adalah edukasi, hiburan, dan pelestarian budaya Indonesia.

---

## 11. Penutup

E-Wayang adalah proyek yang menggabungkan seni budaya, teknologi, dan interaksi manusia dalam satu pengalaman digital yang menarik. Proyek ini cocok untuk digunakan sebagai media pembelajaran, presentasi, atau demonstrasi inovasi berbasis budaya.

**Lestarikan Wayang, Lestarikan Budaya!**

---

*Dibuat untuk kebutuhan pengumpulan tugas / presentasi.*
