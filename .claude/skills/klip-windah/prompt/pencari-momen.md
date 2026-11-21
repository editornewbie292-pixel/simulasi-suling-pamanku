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

## Prompt A - cari kandidat dari 1 VOD Windah

```
Kamu pencari kandidat momen untuk program clipper resmi Windah Basudara GTA VI.
Saya kirim 1 link VOD. Pindai TRANSKRIP per segmen 3 jam (00:00–03:00, 03:00–06:00,
dst.) supaya tidak ada bagian yang terlewat. Laporkan segmen mana yang sudah
dipindai dan mana yang belum.

Klip yang meledak (>100 rb views) BUKAN yang efeknya ramai, tapi yang KONSEPNYA
langsung kebaca dari satu judul. Topik umum (top 5, kompilasi, "ada lagu indo")
SELALU flop. Cari MOMEN SPESIFIK dengan pola berikut (prioritas dari atas):

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
      "kategori": "banding | sus | ironi | drama | ekspektasi_realita | panik_lucu",
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
