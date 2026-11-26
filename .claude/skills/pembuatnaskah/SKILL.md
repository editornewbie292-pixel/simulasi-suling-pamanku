---
name: pembuatnaskah
description: Menulis naskah narasi cerita hikmah berbahasa Indonesia untuk video animasi kartun 3D kampung (5-10 menit, 16:9), dengan pola "Tiga Nasihat" - hook dari klimaks lalu mundur ke awal, tiga ujian yang makin berat dengan refrein, benda kecil yang ditanam lalu dibayar, twist ganda, moral satu kalimat, CTA kanal. Pakai setiap kali pengguna minta "naskah baru", "bikin naskah cerita", "cerita hikmah", "naskah pola tiga nasihat", atau menjalankan /pembuatnaskah dengan ide/tema/moral.
---

# pembuatnaskah

Pengguna memberi ide, tema, atau moral; Claude menulis naskah narasi **asli** yang mengikuti pola video
referensi "Tiga Nasihat" (dianalisis 26 Nov 2026). Hanya polanya yang ditiru - jangan menyalin tokoh, kejadian,
benda, atau kalimat dari cerita referensi (`referensi/tiga-nasihat.md`).

## Alur kerja
1. **Baca permintaan.** Bila pengguna sudah memberi ide/moral, langsung tulis. Tanyakan (AskUserQuestion, maks 3
   pertanyaan) hanya yang benar-benar kurang:
   - **moral / pelajaran** inti (mis. sabar, jujur, berbakti, jangan serakah);
   - **durasi**: pendek ~5 menit (~600 kata) atau penuh ~9 menit (~1.150 kata). Bawaan: penuh;
   - **latar** (bawaan: kampung Jawa/Nusantara zaman dulu, tanpa ponsel).
   Bila pengguna hanya bilang "naskah baru" tanpa ide, tawarkan 3 premis singkat (1-2 kalimat + moral) untuk dipilih.
2. **Rancang dulu (tidak perlu ditampilkan panjang):** tokoh utama + kebutuhannya, pemberi ujian/nasihat,
   3 ujian, benda tanaman, salah paham di klimaks, dua twist, moral. Isi daftar periksa di bawah.
3. **Tulis naskah** dengan format keluaran di bawah.
4. **Simpan** ke `naskah/<judul-singkat>.md` di akar repo, lalu kirim isinya di chat. Tawarkan revisi
   (judul, twist, panjang, nama tokoh).

## Struktur (proporsi dari referensi 9:27, ~125 kata/menit)
| # | Bagian | Porsi | Isi wajib |
|---|---|---|---|
| 1 | **Hook - cuplikan klimaks** | 5% (~30 dtk) | Buka dengan angka/waktu + situasi paling tegang dari bagian 7, berhenti tepat sebelum tokoh bertindak. Kalimat terakhir menyebut "harga" atau rahasia yang membuat penasaran. |
| 2 | **Kartu judul** | - | JUDUL 2-3 kata + subjudul pendek yang menyebut harganya (mis. "seharga 20 tahun"). |
| 3 | **Latar + janji** | 10% | "Semua ini berawal ..." Tokoh miskin/sederhana, detail indra konkret, sebuah **janji**, dan **benda tanaman** diletakkan dengan pesan ("simpan ini, nanti ..."). Satu kalimat pertanda: "Dia belum tahu, ..." |
| 4 | **Bangun kredibilitas sang pemberi** | 10% | Tokoh bijak yang aneh/sedikit bicara. Satu kejadian kecil yang membuktikan ucapannya selalu benar (orang-orang menertawakan, lalu terbukti). Lompatan waktu berulang ("setahun, lima tahun, sepuluh tahun"). |
| 5 | **Dilema inti** | 18% | Pilihan yang tampak bodoh: hasil kerja nyata vs sesuatu yang tak berwujud (nasihat, janji, kebaikan). Narator menyuarakan keraguan penonton ("kalau dilihat dari ..., jelas dia orang paling bodoh ..."). Tokoh pulang/berangkat hampir tanpa apa-apa + satu **benda tertutup** dengan larangan ("jangan dibuka di jalan"). |
| 6 | **Ujian 1 dan 2** | 2 x 11% | Tiap ujian: godaan yang masuk akal -> tokoh teringat nasihat (kutip ulang persis) -> memilih jalan sulit -> akibat bagi yang memilih lain terungkap -> refrein **"Nasihat pertama, terbukti."** Ujian 2 lebih berbahaya dan menyambung ke ujian 1 (benda/tokoh dari ujian 1 muncul lagi). |
| 7 | **Ujian 3 = klimaks** | 20% | Kembali ke adegan hook dengan kalimat yang sama. Taruhan paling pribadi (keluarga, harga diri). Salah paham besar yang dipicu benda tanaman. Tokoh menahan diri. Dialog dari pihak lain pelan-pelan membalik salah paham -> **twist 1**. Reaksi fisik tanpa kata (menangis tanpa suara). |
| 8 | **Resolusi + twist 2** | 11% | Pertemuan/pengakuan. Benda tertutup dibuka: isinya membalik makna pengorbanan (ternyata tidak rugi). Ulangi kalimat deskripsi dari bagian 5 persis sama. Sang pemberi ternyata melindungi/menguji, bukan mengambil. |
| 9 | **Moral + CTA** | 3% | "Ternyata, ..." + moral satu kalimat yang bisa dikutip. Tutup: "Masih banyak cerita hikmah lain di kanal ini. Sampai jumpa di cerita berikutnya." |

## Daftar periksa (semua harus ada)
- [ ] Hook = potongan klimaks, dan klimaks memakai kalimat hook yang sama saat cerita kembali ke sana.
- [ ] Minimal **3 benda tanaman** yang dibayar: satu memicu salah paham, satu jadi pengenal/penanda, satu jadi twist (benda tertutup).
- [ ] Satu **kalimat deskripsi kembar** (muncul di dilema dan di resolusi, kata per kata sama).
- [ ] Tiga ujian naik taruhan: harta -> nyawa/keselamatan -> keluarga/hubungan.
- [ ] Refrein "Nasihat ke-__, terbukti." (atau padanan sesuai cerita) setelah ujian 1 dan 2; ujian 3 dibayar oleh twist, bukan refrein.
- [ ] Nasihat/aturan dikutip ulang persis saat tokoh mengingatnya.
- [ ] Ironi dramatis di klimaks: penonton ikut salah paham sampai dialog membaliknya.
- [ ] Dua twist; twist kedua mengubah cara pandang terhadap tokoh bijak.
- [ ] Tidak ada kekerasan yang benar-benar terjadi pada tokoh utama; ketegangan dari niat yang ditahan.
- [ ] Nama tokoh lokal sederhana (2-3 suku kata), panggilan kekerabatan (Kang, Ki, Pak, Mbok, Le/Nduk, Juragan).

## Gaya bahasa
- **Satu baris = satu ketukan narasi, 2-8 kata.** Kalimat panjang dipecah: "Kakinya lecet. / Sandalnya putus."
  Naskah dibaca narator + jadi subtitle karaoke 2-4 kata.
- **Pengulangan berirama** untuk tegang dan waktu: "makin erat, makin erat"; "20 tahun dia ... 20 tahun dia ...".
- **Tag dialog eksplisit** di baris sendiri ("Jumadi berkata," / "Juragan menjawab.") karena satu narator.
- Narasi baku-santai ("nggak", "gak", "cuma"); dialog boleh berwarna daerah ringan. Hindari kata asing.
- Detail indra konkret dan murah: bunyi hujan "tes, tes, tes", bau makanan, berat kantong, rasa perih.
- Waktu cerita sebelum ada ponsel/surat sulit sampai - alasan tokoh tidak bisa memberi kabar.

## Format keluaran
```markdown
# JUDUL
Subjudul kartu judul · Moral: ... · Perkiraan durasi: ~9 menit (~1.150 kata)

## Tokoh
- Nama - peran, ciri visual singkat (untuk animasi: pakaian, topi, kumis, kacamata)

## Benda tanaman
- Benda - ditanam di bagian __, dibayar di bagian __

## Naskah
### 1. Hook (0:00)
[Adegan: lokasi, waktu, ekspresi/kamera singkat]
Baris narasi.
Baris narasi.

### 2. Kartu judul
JUDUL — subjudul

### 3. Latar (0:30)
...
```
- Tiap bagian diberi perkiraan waktu mulai (hitung ~125 kata/menit).
- Catatan adegan `[Adegan: ...]` singkat, tiap pergantian lokasi/suasana: tempat, terang/gelap/hujan, ekspresi
  kunci (kaget, menangis, marah), efek khusus bila perlu (speed lines saat teringat, layar terbelah saat
  membandingkan wajah). Cocok dengan gaya animasi kartun 3D kampung (lihat skill gaya-miko1).
- Dialog di baris sendiri setelah tag-nya; tanpa tanda kutip berlebihan.
- Akhiri dengan 3 usulan judul video YouTube + 1 kalimat deskripsi.

## Referensi
`referensi/tiga-nasihat.md`: peta beat video referensi + contoh teknik per bagian. Baca bila ragu soal pola.
