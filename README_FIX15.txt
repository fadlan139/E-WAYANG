BIMA DAN ARJUNA – JANJI DI TENGAH HUTAN – FIX15

Perbaikan utama:
1. Memperbaiki crash saat masuk dialog Adegan 1:
   ValueError: too many values to unpack (expected 2)
   Setiap dialog sekarang dibaca sebagai 3 data: speaker, teks, file audio.
2. Sinkronisasi teks narator menggunakan durasi audio MP3 yang sebenarnya.
   Teks narator dibagi per kalimat lalu muncul bertahap mengikuti progres voice.
3. Pergantian narasi dan dialog menggunakan durasi Sound yang terukur + buffer kecil,
   sehingga tidak bergantung pada channel busy yang bisa berubah karena timing mixer.
4. Perpindahan adegan diberi log [SCENE] di terminal untuk memudahkan pengecekan.
5. Audio dialog tetap mengikuti durasi masing-masing file, bukan timer 5.5 detik.

Jalankan dengan run.bat.
Pastikan menggunakan folder FIX15, bukan folder FIX14 lama.
