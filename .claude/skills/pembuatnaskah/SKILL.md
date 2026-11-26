---
name: pembuatnaskah
description: Menulis naskah narasi cerita hikmah berbahasa Indonesia untuk video animasi kartun 3D (5-10 menit) yang membuat penonton tidak skip - dibangun dari ALASAN kenapa cerita viral seperti "Tiga Nasihat" digemari (hook ketakutan universal, dilema yang diperdebatkan penonton, jawaban+pertanyaan baru tiap 1-1,5 menit, emosi dibalik, rasa adil, kalimat yang layak dibagikan), bukan menyalin bentuknya. Pakai setiap kali pengguna minta "naskah baru", "bikin naskah cerita", "cerita hikmah", atau menjalankan /pembuatnaskah dengan atau tanpa ide.
---

# pembuatnaskah

Tugasnya bukan meniru satu cerita, tapi membuat penonton **tidak menggeser layar** dari detik pertama sampai
CTA. Pengguna menegaskan: naskah jangan "plek ketiplek", harus bisa improvisasi, dan Claude harus berpikir
**kenapa** sebuah cerita digemari warganet. Bentuk boleh apa saja; efek di bawah ini wajib tercapai.

## Kenapa cerita seperti ini tidak di-skip (mesinnya)
1. **Hook menyentuh ketakutan universal** dalam 5 detik: keluarga, harga diri, uang, nyawa, aib. Pakai angka
   konkret. Hook meninggalkan **dua pertanyaan** yang baru dijawab jauh di belakang (umumnya di 2/3 cerita).
2. **Dekat dengan hidup penonton.** Merantau, rumah bocor, utang, anak jarang pulang, orang tua sakit, sekolah
   tak terbayar. Penonton harus melihat keluarganya sendiri, bukan sekadar menonton tokoh.
3. **Penonton ikut memilih.** Ada satu pilihan yang tampak bodoh/merugikan, dan penonton dalam hati berkata
   "kalau aku sih ...". Pertanyaan "pilihannya benar nggak?" menahan bagian tengah dan memancing komentar.
4. **Tidak ada bagian mati.** Setiap 60-90 detik satu pertanyaan terjawab dan satu yang baru dibuka. Tiap
   babak terasa seperti cerita mini utuh. Di titik rawan skip (pergantian babak) taruh **kalimat pengait**:
   "Dia belum tahu ...", "Tapi ... belum selesai bicara.", "Dan itu baru permulaan."
5. **Penonton dibuat merasa pintar.** Beri penonton petunjuk lebih dulu daripada tokohnya (benda, wajah,
   kalimat yang muncul lagi), biarkan mereka menyambungkan sendiri.
6. **Ada janji yang ditunggu.** Bila memakai hook dari tengah/akhir cerita, penonton tahu adegan itu akan
   kembali; makin dekat, makin tegang. Saat kembali, ulangi kalimat hook-nya.
7. **Emosi penonton dibalik.** Giring penonton ikut curiga/marah/menghakimi, lalu satu informasi membaliknya
   menjadi malu, haru, atau lega. Pergantian mendadak ini yang membuat orang menangis dan membagikan.
8. **Rasa takut rugi dibayar lunas.** Pengorbanan yang dikhawatirkan penonton harus terbayar di akhir
   (orang baik tidak dirugikan, yang curang kena akibat). Penonton menutup video dengan lega.
9. **Pesan praktis yang layak dibagikan.** Satu kalimat moral yang bisa dikutip dan dikirim ke grup keluarga;
   cerita aman ditonton semua umur.
10. **Mudah diikuti sambil lalu.** Kalimat pendek, hal penting diulang, subtitle. Penonton yang menonton sambil
    masak tetap tidak ketinggalan.

## Yang bebas diimprovisasi (dan HARUS berbeda dari naskah sebelumnya)
- **Bentuk alur**: hook dari klimaks lalu mundur; maju lurus dengan bom waktu; dua garis waktu bergantian;
  diceritakan dari sudut tokoh yang salah paham; berbingkai (orang tua bercerita ke cucu); hitung mundur.
- **"Harga" yang dibayar tokoh**: uang, waktu, harga diri, kesempatan, kebenaran yang disimpan, janji.
- **Jumlah ujian/babak**: 2-4, atau tanpa ujian berpola sama sekali.
- **Siapa yang berubah**: tokoh utama, tokoh yang membenci, penonton sendiri.
- **Jenis twist**: identitas, makna kalimat/benda dari awal berubah, siapa sebenarnya yang berutang/bersalah,
  waktu (ternyata sudah terjadi), motif tokoh "jahat" ternyata melindungi.
- **Latar**: kampung zaman dulu, pasar, pelabuhan, sawah, kota kecil tahun 90-an, perantauan; tetap Nusantara
  dan mudah digambar sebagai animasi kartun 3D.
- Tokoh bijak, benda tertutup, refrein: **alat, bukan kewajiban**. Pakai hanya bila cocok.
Sebelum menulis, cek `naskah/` di akar repo: naskah baru tidak boleh memakai bentuk alur + jenis twist +
"harga" yang sama dengan naskah yang sudah ada.

## Alur kerja
1. **Baca permintaan.** Ada ide/moral: langsung rancang. Tanpa ide: tawarkan 3 premis berbeda bentuk
   (1-2 kalimat + hook + moral) lewat AskUserQuestion. Tanyakan durasi hanya bila tidak jelas
   (bawaan ~6-9 menit; ~125 kata/menit).
2. **Rancang dulu**: ketakutan di hook + dua pertanyaannya, pilihan yang diperdebatkan, babak-babak dengan
   jawaban/pertanyaan baru tiap 60-90 detik, petunjuk untuk penonton, momen pembalikan emosi, pembayaran
   rasa adil, kalimat moral. Pilih bentuk alur dan twist yang belum dipakai.
3. **Tulis naskah** (format di bawah), lalu **uji per babak**: "Di detik ini, kenapa penonton tetap menonton?"
   Bila jawabannya tidak ada, perbaiki babak itu.
4. **Simpan** ke `naskah/<judul-singkat>.md`, kirim filenya (SendUserFile), dan di chat beri ringkasan cerita +
   tabel singkat efek mana ada di bagian mana. Tawarkan revisi.

## Gaya bahasa
- Satu baris = satu ketukan narasi, 2-8 kata ("Kakinya lecet. / Sandalnya putus."). Narator tunggal; dialog di
  baris sendiri setelah tag ("Pak Darto menjawab,").
- Pengulangan berirama untuk tegang/waktu ("makin erat, makin erat"; "setahun, lima tahun, sepuluh tahun").
- Narasi baku-santai ("nggak", "cuma"); dialog boleh berwarna daerah ringan (Le, Nduk, Kang, Mbok, Ki, Juragan).
- Detail indra konkret dan murah: bunyi ("tes, tes, tes", "ting"), bau, berat, perih, lapar.
- Tanpa kekerasan grafis; ketegangan dari niat, rahasia, dan waktu.

## Format keluaran
```markdown
# JUDUL
Subjudul kartu judul · Moral: ... · Perkiraan durasi: ~N menit (~K kata)

## Tokoh
- Nama - peran, ciri visual singkat untuk animasi

## Benda / petunjuk tanaman
- Benda/kalimat - ditanam di bagian __, dibayar di bagian __

## Naskah
### 1. <nama bagian> (0:00)
[Adegan: tempat, waktu/cuaca, ekspresi atau kamera kunci]
Baris narasi.
...
```
- Waktu mulai tiap bagian dihitung dari jumlah kata (~125 kata/menit), bukan ditebak.
- Catatan `[Adegan: ...]` singkat tiap ganti lokasi/suasana; boleh efek (speed lines saat teringat, layar
  terbelah, close-up benda tanaman). Cocok dengan gaya kartun 3D kampung (skill gaya-miko1).
- Akhiri dengan 3 usulan judul YouTube + 1 kalimat deskripsi. CTA penutup kanal: "Masih banyak cerita hikmah
  lain di kanal ini. Sampai jumpa di cerita berikutnya." (boleh didahului ajakan bertindak, mis. "Telepon
  bapakmu hari ini.")

## Contoh (bentuknya sengaja berbeda - jangan disalin)
- `referensi/tiga-nasihat.md`: video referensi yang digemari warganet. Hook klimaks lalu mundur, tokoh bijak,
  tiga ujian ber-refrein, twist identitas + harta kembali.
- `naskah/utang-bapak.md` (akar repo): hook pemakaman lalu mundur, tanpa tokoh bijak dan tanpa pola ujian,
  yang berubah adalah tokoh yang membenci, twist mengubah makna kalimat dari awal ("orang yang belum kita kenal").
