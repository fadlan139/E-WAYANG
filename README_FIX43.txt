FIX43 - Wayang bisa bergerak (rig lengan + badan) seperti video referensi

APA YANG BERUBAH
- Wayang kini terdiri dari bagian: badan, lengan atas, lengan bawah+tangan (assets/rig/<nama>/).
- Badan mengikuti telapak tangan, miring mengikuti putaran tangan, berayun saat bergerak,
  dan ada gerak napas pelan.
- Lengan depan mengikuti arah jari (IK dua tulang, siku menekuk otomatis) dan memanjang/memendek
  sesuai seberapa jauh jari direntangkan.
- Ada gapit (tongkat) badan dan tuding di tangan seperti di video.
- Wayang tanpa rig (mis. arjuna_new.png) tetap tampil statis seperti sebelumnya, tidak error.

KONFIGURASI (config.json -> "rig")
  enabled     : true/false, matikan rig untuk kembali ke wayang statis
  arm_driver  : "thumb" (lengan ikut arah jempol) atau "index" (lengan ikut telunjuk)
  rods        : true/false, tampilkan gapit
  arm_smooth  : 0.1 - 0.6, makin besar makin responsif
  roll_gain   : kemiringan badan dari putaran tangan
  sway_gain   : ayunan badan saat tangan bergeser

MEMBUAT RIG UNTUK WAYANG LAIN
1. Buka tools/make_rig.py, tambahkan entri di RIGS (titik bahu, siku, tangan, garis potong bahu).
2. python tools/make_rig.py nama_aset
3. python tools/preview_rig.py nama_aset   -> gambar pratinjau pose (tanpa kamera)
Opsi tambahan di make_rig.py: poly (lengan dipilih lewat poligon), erase (hapus tongkat bawaan
gambar), keep_shoulder (sisakan sendi bahu), body_rod (False bila gambar sudah punya gapit badan).

Aset yang sudah punya rig: bima_new, werkudara_new, arjuna_new, kapi_angeni.
Semar (semar.png) belum diberi rig karena posenya duduk melingkar dan lengannya tidak punya
bentuk bahu-siku-tangan yang jelas; tetap tampil statis.

PERBAIKAN FULLSCREEN / MAXIMIZE
- Sebelumnya tampilan selalu digambar 1280x720 di pojok kiri atas, jadi saat jendela di-maximize
  atau F11 sisanya hitam dan tampilan terlihat "kepotong".
- Sekarang semua digambar ke kanvas 1280x720, lalu diskalakan memenuhi jendela dengan menjaga
  rasio 16:9 (jika layar bukan 16:9, ada pita hitam tipis di tepi, isi tidak terpotong).
- Klik dan hover mouse otomatis disesuaikan dengan skala, jadi tombol tetap tepat di semua ukuran.
- F11 memakai resolusi asli monitor. Tekan F11 lagi untuk kembali ke jendela.

BACKGROUND BATIK (Menu Utama dan Gesture Attack)
- Foto baru: assets/bg_batik_ui.jpg (kunci "ui_batik" di BG_FILES pada main.py).
- Dipakai di Menu Utama dan Gesture Attack. Mode Quiz tetap memakai bg_edalang_ui.jpg.
- Warna judul, tagline, teks bawah, garis tengah, dan efek SERANG! disesuaikan agar terbaca di latar krem.
- Garis tepi wayang di Gesture Attack kini cokelat tua (di latar gelap tetap emas).
- Untuk ganti lagi: timpa assets/bg_batik_ui.jpg dengan foto 16:9.

LAYAR PILIH KARAKTER (gaya galeri karakter)
- Kiri: grid kartu karakter (potret + nama). Tengah: pratinjau besar karakter aktif dengan cahaya emas.
  Kanan: nama, sifat, dan pilihan pemain. Tombol kembali (panah) di pojok kanan atas.
- Nama slot diganti: "Slot Kiri/Kanan" menjadi "PEMAIN 1" dan "PEMAIN 2" (juga di header Gesture Attack).
- Lencana 1 dan 2 di kartu menunjukkan karakter yang sedang dipakai tiap pemain.
- Pemain 1 / Pemain 2 bisa diklik langsung, atau tekan tombol 1 dan 2. Klik kartu untuk memilih karakter.
- Gambar dan font di-cache supaya layar ini lebih ringan.
