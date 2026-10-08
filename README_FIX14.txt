FIX14 - Bima dan Arjuna

Perbaikan utama:
1. Teks narator tidak lagi menampilkan seluruh paragraf sekaligus.
2. Narasi dipecah berdasarkan kalimat dan setiap kalimat mendapat durasi berdasarkan jumlah kata dibanding durasi audio asli.
3. Perpindahan narasi -> dialog menunggu durasi audio sebenarnya + sedikit buffer.
4. Kamera diturunkan ke 640x480 dan MediaPipe diproses setiap 2 frame agar program tidak berat/stuck di adegan 1.
5. Dialog tetap otomatis maju setelah audio selesai; SPACE tetap bisa digunakan untuk melewati dialog.
6. Narasi akhir, pesan moral, dan penutup juga menggunakan sistem timing yang sama.

Cara menjalankan:
- Buka folder wayang_bima_arjuna_final
- Jalankan run.bat
- Atau: python main.py

Jika kamera membuat program berat, jalankan:
python main.py --camera 0

Tombol:
SPACE = lanjut dialog
N = lewati narasi/tahap tertentu
F11 = fullscreen
ESC = keluar
