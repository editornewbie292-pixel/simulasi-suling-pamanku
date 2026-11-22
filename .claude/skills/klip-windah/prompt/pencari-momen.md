# Prompt untuk AI pencari momen milik pengguna

Kemampuan AI pengguna (hasil uji 20 Nov 2026): membaca transkrip YouTube + timestamp (Bahasa Indonesia), meleset
±5-30 detik (VOD 10+ jam bisa 30-60 detik), visual jarang dianalisis pada VOD panjang, TIDAK bisa membaca live chat,
TIDAK bisa memberi screenshot/MP4, optimal 1 link per giliran dan dipindai per segmen 3 jam.

Pembagian kerja: AI pengguna mencari kandidat (JSON) -> pengguna merekam layar dengan buffer -20/+40 detik ->
Claude mencari momen presisi dari rekaman (puncak suara, beda frame/WASTED, Whisper) -> edit.
Saat menerima JSON: pilih 2-3 kandidat terkuat. Prioritas (dari analisis 5 video >100 rb views, 21 Nov 2026):
banding (adegan sama dengan streamer lain) > sus (sindiran 18+, bukan eksplisit) > ironi/drama > ekspektasi_realita.
Abaikan yang keyakinan_timestamp "rendah" kecuali skornya tinggi, dan minta pengguna merekam per id klip.
Kandidat "banding" butuh rekaman streamer lain di adegan yang sama -> pakai Prompt B.

Pola viral (21 Nov 2026): konsep > efek. Bar judul statis yang menjanjikan konflik ("PERBEDAAN X & WINDAH PAS ...",
"STREAMER LAIN KETIKA ...", "WINDAH TRAGEDI ..."), tanpa VO dan tanpa kartu hook animasi, 35-60 dtk, ending
punchline. Topik umum ("TOP 5 ...", "ADA LAGU INDO") flop - yang meledak selalu momen SPESIFIK yang kontras.

Strategi per platform (riset pengguna 22 Nov 2026):
- TikTok: SIMPEL POLOS (bar judul / kartu hook sederhana) pada momen SUS dan momen IKONIK (adegan yang semua orang
  bicarakan: misi besar, cutscene, bug terkenal, "mobil bang YB", lonjakan GG ratusan orang di chat).
- YouTube Shorts: hashtag yang sama jarang tembus 100 rb; yang tertinggi (~40 rb) = CERITA ULANG momen dengan
  VO pengguna + SFX + meme pekat (trollface, Patrick pura-pura gak liat, tanda "?", orang ketawa nunjuk) +
  kolase gambar di hook. Momen cocoknya: kejadian beruntun yang bisa dinarasikan (bug, ngeles, salah paham, sial).
- Pemantau live chat (`scripts/pantau_chat.py`) = penanda waktu nyata; Prompt A/C di VOD = konteks & kutipan.

## Prompt A - cari kandidat dari 1 VOD Windah

```
Kamu pencari kandidat momen untuk program clipper resmi Windah Basudara GTA VI.
Saya kirim 1 link VOD. Pindai TRANSKRIP per segmen 3 jam (00:00–03:00, 03:00–06:00,
dst.) supaya tidak ada bagian yang terlewat. Laporkan segmen mana yang sudah
dipindai dan mana yang belum.

Klip yang meledak (>100 rb views) BUKAN yang efeknya ramai, tapi yang KONSEPNYA
langsung kebaca dari satu judul. Topik umum (top 5, kompilasi, "ada lagu indo")
SELALU flop. Cari MOMEN SPESIFIK dengan pola berikut (prioritas dari atas):

0. IKONIK – adegan yang akan dibicarakan semua orang: misi/cutscene besar, pertama kali
   bertemu karakter/kendaraan terkenal, bug lucu, momen yang membuat Windah teriak/tertawa
   panjang. Isi platform "tiktok" (polos) atau "keduanya" bila bisa diceritakan ulang.
1. BANDING – adegan yang PASTI dialami streamer lain juga, tapi versi Windah beda/
   kacau/ironis: misi cerita & cutscene (sebut nama misinya), tutorial pertama
   (terbang/landing, menyetir pertama, benerin sesuatu, mancing), momen awal/akhir
   stream (buka stream, end stream, jumlah viewer), bos/kejar-kejaran ikonik.
   Pemicu transkrip: Windah gagal di bagian yang "harusnya gampang", "kok gue beda",
   "yang lain gimana", menyebut streamer lain, atau adegan yang jelas dari misi utama.
2. SUS 18+ (SINDIRAN, BUKAN EKSPLISIT) – NPC perempuan/klub/kamar/pantai/bikini,
   kalimat bermakna ganda ("pipa", "masuk", "basah", "keras", "dari belakang",
   "pegang"), Windah salah tingkah ("jangan liat", "astaghfirullah", "sensor",
   "anak kecil tutup mata", bengong lama, "ih", tertawa malu). Tandai tingkat_sus.
   Yang eksplisit (telanjang/adegan seks jelas) JANGAN diusulkan.
3. IRONI / SARKAS – kontras angka/nasib ("viewer paling sepi", "padahal ...",
   "percuma ..."), Windah menyindir diri sendiri atau penonton, roleplay dimarahi.
4. DRAMA / CURHAT – opini kuat soal uang/AdSense/promosi/copyright/replay/kritik
   penonton/haters, kalimat yang memancing debat di komentar.
5. EKSPEKTASI VS REALITA – sesumbar ("gampang", "perfect", "liat nih", "aman")
   lalu dalam 5–60 detik gagal ("WASTED", "mati", "anjir", "loh loh", tawa).
6. PANIK / LUCU – teriak berulang, umpatan kaget, bug/NPC absurd, tawa panjang.

SYARAT: hanya stream GTA VI channel resmi Windah Basudara; klip WAJIB ada
gameplay (bukan cuma ngobrol depan cam); abaikan menu panjang, loading, iklan;
momen 15–60 detik dari pemicu sampai punchline. Momen harus SPESIFIK: kalau
judulnya bisa dipakai untuk 100 klip lain, berarti terlalu umum – buang.

OUTPUT: tabel ringkas, lalu JSON persis dengan skema ini:
{
  "video_url": "",
  "judul_video": "",
  "durasi_total": "hh:mm:ss",
  "segmen_dipindai": ["00:00:00-03:00:00"],
  "segmen_belum": [],
  "klip": [
    {
      "id": 1,
      "kategori": "sus | ikonik | banding | ironi | drama | ekspektasi_realita | panik_lucu",
      "platform": "tiktok | yt_shorts | keduanya",
      "pemicu": "hh:mm:ss",
      "rekam_mulai": "hh:mm:ss (pemicu - 20 detik)",
      "rekam_selesai": "hh:mm:ss (pemicu + 40 detik)",
      "kutipan": "ucapan Windah persis dari transkrip",
      "dugaan_kejadian": "apa yang kemungkinan terjadi di game (tandai 'dugaan')",
      "nama_adegan": "nama misi/cutscene/aktivitas (untuk dicari di VOD streamer lain)",
      "punchline": "kalimat/reaksi penutup",
      "judul_bar": ["PERBEDAAN ... & WINDAH PAS ...", "alternatif"],
      "ending_ide": "wasted | get_out | meanwhile | punchline_kalimat",
      "tingkat_sus": "tidak | ambigu | nyerempet",
      "meme_ide": [{"detik": "hh:mm:ss", "momen": "Windah ngeles", "keyword_meme": "patrick pura pura gak liat"}],
      "skor": 1-10,
      "alasan_skor": "kenapa orang awam langsung paham & penasaran dari judulnya",
      "keyakinan_timestamp": "tinggi | sedang | rendah"
    }
  ]
}
Urutkan dari skor tertinggi, maksimal 10 klip per segmen. Skor tinggi hanya untuk
momen yang konsepnya kebaca dari judul_bar saja. Jangan mengarang: bila transkrip
tidak jelas, tulis "tidak terbaca" dan turunkan keyakinan.
```

## Prompt B - cari adegan yang sama di VOD streamer lain (untuk format banding)

```
Saya sedang membuat klip perbandingan "streamer lain vs Windah Basudara" di GTA VI.
Adegan yang dicari: <nama_adegan dari Prompt A, mis. "misi benerin pipa (Hector)">.
Kutipan/dugaan kejadian di versi Windah: <kutipan + dugaan_kejadian>.

Saya kirim 1 link VOD streamer lain. Cari di transkrip kapan dia memainkan adegan
yang SAMA (dialog NPC/misi yang sama, tempat yang sama). Pindai per segmen 3 jam.

OUTPUT JSON:
{
  "video_url": "",
  "streamer": "",
  "adegan": "",
  "ketemu": true,
  "mulai_adegan": "hh:mm:ss",
  "rekam_mulai": "hh:mm:ss (mulai_adegan - 20 detik)",
  "rekam_selesai": "hh:mm:ss (mulai_adegan + 60 detik)",
  "penanda_dialog": "kalimat NPC/game yang sama persis di kedua VOD (untuk sinkron)",
  "versi_streamer_ini": "apa yang dia lakukan/ucapkan - normal/mulus/beda dari Windah?",
  "kontras": "kenapa perbandingannya lucu/ironis (1 kalimat)",
  "keyakinan_timestamp": "tinggi | sedang | rendah"
}
Kalau adegannya tidak ada, tulis "ketemu": false dan sebut segmen yang sudah dipindai.
Jangan mengarang timestamp.
```

## Prompt C - cari momen "cerita ulang" untuk YouTube Shorts (VO + meme)

```
Saya membuat YouTube Shorts gaya "cerita ulang" dari stream GTA VI Windah Basudara:
narasi suara (VO) + SFX + meme. Dari transkrip VOD berikut, cari 5-10 momen yang
punya ALUR (awal -> kejadian aneh/sial/ngeles -> reaksi Windah -> punchline), 30-60
detik, yang enak dinarasikan dalam 3-6 kalimat. Contoh bagus: Windah nemu bug lalu
ngeles, salah paham dengan NPC, rencana gagal beruntun, barang hilang lalu muncul.

Untuk tiap momen beri JSON:
{"id":1, "mulai":"hh:mm:ss", "selesai":"hh:mm:ss", "judul_hook":"WINDAH NEMU BUG",
 "alur":["setup","kejadian","reaksi","punchline"],
 "kutipan_kunci":["ucapan Windah persis + hh:mm:ss"],
 "naskah_vo":["kalimat narasi 1 (gaya santai, bahasa gaul)", "..."],
 "meme_ide":[{"detik":"hh:mm:ss","momen":"Windah pura-pura nggak lihat",
              "keyword_meme":"patrick pura pura gak liat"}],
 "skor":1-10, "keyakinan_timestamp":"tinggi|sedang|rendah"}
Jangan mengarang kutipan; tandai bagian yang tidak jelas.
```
