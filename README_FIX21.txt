Bima dan Arjuna – FIX21

Perbaikan utama:
1. Memperbaiki crash narration_sentence_state:
   ValueError: not enough values to unpack (expected 3, got 2)
   Timing (start, end) sekarang dinormalisasi menjadi (sentence, start, end).
2. Jika tabel timing rusak/tidak cocok, program otomatis memakai fallback dan tidak berhenti.
3. Kalimat narator panjang tidak lagi dipotong menjadi hanya 3 baris; maksimal 4 baris ditampilkan.
4. Panel narasi diperbesar agar seluruh kalimat panjang terlihat.
5. Timing subtitle tetap mengikuti batas audio yang sudah ditentukan agar teks tidak berpindah sebelum kalimat suara selesai.

Jalankan run.bat.
