FIX20 - Perbaikan sinkronisasi subtitle dan audio

Perbaikan utama:
1. Teks pembukaan sekarang SAMA PERSIS dengan rekaman 01_pembukaan.mp3:
   - Di sebuah hutan yang jauh dari keramaian, dua kesatria sedang menempuh perjalanan panjang.
   - Bima dan Arjuna berjalan bersama, melewati pepohonan yang lebat dan jalan setapak yang sunyi.
   - Namun, perjalanan mereka tidak selalu berjalan mudah. Di tengah hutan, mereka harus menghadapi sebuah pilihan yang menguji kesabaran, keyakinan, dan hubungan di antara mereka.
   - Akankah mereka mampu menemukan jalan yang benar?
   - Dan mampukah mereka tetap saling percaya, meskipun memiliki pendapat yang berbeda?
2. Subtitle pembukaan memakai timestamp berdasarkan jeda aktual audio, sehingga tidak lagi mengikuti pembagian jumlah kata yang menyebabkan teks tertinggal.
3. Subtitle narasi tiap adegan memakai timestamp yang sudah disesuaikan dengan jeda audio.
4. Fade subtitle dipercepat agar teks muncul hampir bersamaan dengan suara, tetapi tetap halus.
5. Pemetaan audio Arjuna Adegan 2 diperbaiki sesuai kondisi file yang dilaporkan:
   - arjuna_03.mp3 -> "Jangan terburu-buru, Bima. Kita tidak tahu apakah jalan itu benar."
   - arjuna_02.mp3 -> "Keyakinan itu baik, tetapi kita juga harus menggunakan akal."

Catatan:
Jika setelah FIX20 suara Arjuna masih tertukar, berarti isi file MP3-nya sendiri yang tertukar. Dalam kasus itu kirim dua file suara Arjuna tersebut dan saya akan sesuaikan tanpa mengubah teks.
