# Bima dan Arjuna – Janji di Tengah Hutan
## FIX16 – Sinkronisasi audio, teks, dan urutan adegan

Versi ini dibuat dari program FIX15 yang kamu kirim dan memperbaiki bug yang terlihat pada rekaman.

### Perbaikan utama
- Setiap dialog memakai **timer audio sendiri**. Timer dialog sebelumnya tidak lagi diwariskan ke dialog berikutnya.
- Program tidak boleh menganggap dialog selesai sebelum file voice yang sedang diputar benar-benar selesai.
- `SPACE` tidak lagi dapat memotong atau melewati voice yang sedang berjalan.
- Tombol `N` yang sebelumnya berpotensi melewati bagian cerita sekarang dinonaktifkan.
- Semua dialog tetap otomatis lanjut **satu per satu** setelah audio selesai.
- Urutan 5 adegan dikunci: narasi → seluruh dialog → transisi → adegan berikutnya.
- Narasi pembukaan, jeda, narasi adegan, akhir cerita, pesan moral, dan penutup memakai durasi MP3 asli.
- Teks narator menggunakan **cross-fade halus antar kalimat**, bukan pergantian teks mendadak.
- Pembukaan memakai timeline kalimat berdasarkan jumlah kata sehingga pergantian teks mengikuti progres voice.
- Setelah voice selesai, teks tidak langsung dipotong.
- Ditambahkan validasi awal untuk memastikan semua file audio, background, dan format dialog tersedia sebelum cerita dimulai.
- Tracking kamera/MediaPipe tetap terisolasi dari alur cerita agar error kamera tidak memutus cerita.
- Judul tetap menggunakan efek layar menggelap + fade/zoom.
- Ending tetap: Bima dan Arjuna menjauh → musik → fade gelap → pesan moral akhir → TAMAT.

### Urutan cerita
1. Pembukaan
2. Jeda
3. Kalimat pengantar
4. Judul
5. Adegan 1
6. Adegan 2
7. Adegan 3
8. Adegan 4
9. Adegan 5
10. Akhir cerita
11. Pesan moral
12. Kalimat penutup
13. Ending

### Kontrol
- `SPACE` = lanjut ke dialog berikutnya **setelah voice selesai**
- `F11` = fullscreen
- `P` = mode projector
- `ESC` = keluar

Tidak ada tombol skip otomatis untuk narasi/dialog agar suara tidak terlewat.

### Menjalankan
Jalankan `run.bat` dari folder `wayang_bima_arjuna_final`.

Atau:
`& "C:\Users\labta\AppData\Local\Programs\Python\Python311\python.exe" main.py`

Sebelum cerita dimulai terminal akan menampilkan:
`[CHECK] Semua audio, dialog, dan background ditemukan.`

Kemudian setiap bagian akan dicatat, misalnya:
`[NARRATION] Adegan 1 mulai: 07_adegan1.mp3`
`[DIALOGUE] Adegan 1 | Bima: ...`
`[DIALOGUE] Adegan 1 | Arjuna: ...`
`[SCENE] Masuk adegan 2`

Jika ada masalah lagi, screenshot terminal dengan log tersebut akan menunjukkan tepat bagian yang bermasalah.
