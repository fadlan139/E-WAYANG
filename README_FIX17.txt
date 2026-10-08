# Bima dan Arjuna – FIX17

Perbaikan fokus pada dua masalah: suara/adegan yang terasa terlewat dan teks narator yang tidak smooth.

## Perubahan
- Semua file voice cerita dipreload sebelum cerita dimulai, sehingga loading MP3 tidak terjadi saat pergantian adegan/dialog.
- Timestamp audio dimulai setelah `channel.play()`, bukan sebelum pemutaran channel.
- Narasi tidak lagi mengganti seluruh kalimat secara mendadak. Teks sekarang muncul progresif kata demi kata mengikuti progres durasi MP3, dengan fade halus.
- Setelah narasi selesai ada handoff 0,28 detik sebelum dialog pertama agar frame terakhir narasi tidak bertabrakan dengan dialog.
- Pergantian adegan tetap menunggu voice selesai terlebih dahulu.
- `SPACE` diberi debounce 0,30 detik agar satu tekanan tidak diproses ganda.
- Tidak ada tombol skip untuk narasi/dialog.
- Validasi semua audio/dialog/background tetap dilakukan sebelum cerita mulai.

## Urutan tetap
Pembukaan → jeda → pengantar → judul → Adegan 1 → Adegan 2 → Adegan 3 → Adegan 4 → Adegan 5 → akhir cerita → pesan moral → penutup → TAMAT.

## Menjalankan
Jalankan `run.bat` dari folder `wayang_bima_arjuna_final` atau:
`C:\Users\labta\AppData\Local\Programs\Python\Python311\python.exe main.py`


FIX18: subtitle word-clock follows detected speech window; dialogue text is also revealed word-by-word.
