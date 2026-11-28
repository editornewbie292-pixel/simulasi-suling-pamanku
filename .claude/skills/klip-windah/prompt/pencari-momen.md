# Prompt untuk AI pencari momen milik pengguna

> Penilaian akhir kandidat (oleh Claude) memakai skor 7 kolom di `prinsip-momen-fyp.md` §7 (≥10 prioritas,
> 7-9 layak, ≤6 buang) dan lima tes di §8. Baca file itu sebelum memilih momen dari hasil JSON di bawah.

Kemampuan AI pengguna (hasil uji 20 Nov 2026): membaca transkrip YouTube + timestamp (Bahasa Indonesia), meleset
±5-30 detik (VOD 10+ jam bisa 30-60 detik), visual jarang dianalisis pada VOD panjang, TIDAK bisa membaca live chat,
TIDAK bisa memberi screenshot/MP4, optimal 1 link per giliran dan dipindai per segmen 3 jam.

Pembagian kerja: AI pengguna mencari kandidat (JSON) -> pengguna merekam layar dengan buffer -20/+40 detik ->
Claude mencari momen presisi dari rekaman (puncak suara, beda frame/WASTED, Whisper) -> edit.
Saat menerima JSON: pilih 2-3 kandidat terkuat (kategori ekspektasi_realita/panik paling kuat untuk klip momen),
abaikan yang keyakinan_timestamp "rendah" kecuali skornya tinggi, dan minta pengguna merekam per id klip.

## Prompt

```
Kamu pencari kandidat momen untuk program clipper resmi Windah Basudara GTA VI.
Saya kirim 1 link VOD. Pindai TRANSKRIP per segmen 3 jam (00:00–03:00, 03:00–06:00,
dst.) supaya tidak ada bagian yang terlewat. Laporkan segmen mana yang sudah
dipindai dan mana yang belum.

CARI MOMEN dari pola transkrip berikut (prioritas dari atas):
1. EKSPEKTASI VS REALITA: Windah sesumbar ("gampang", "perfect", "liat nih", "pro",
   "santai", "aman") lalu dalam 5–60 detik ada tanda gagal ("WASTED", "mati",
   "anjir", "loh loh", "kok", tawa panjang).
2. PANIK/TERIAK: kata seru berulang ("woi woi", "lari lari", "anjir anjir",
   "astaga"), kalimat terputus, umpatan kaget.
3. PERTAMA/REKOR: "pertama", "orang pertama", "di Indonesia", "rekor", "dunia".
4. TAKJUB DETAIL GTA 6: "gila", "detail banget", "realistis", "liat ini guys",
   "13 tahun".
5. LUCU/ABSURD: tawa panjang, "kocak", "bug", "NPC", "terbang", "kok gini".
6. EMOSIONAL: terharu, berterima kasih, bangga, soal Rockstar atau penonton.

SYARAT: hanya stream GTA VI channel resmi Windah Basudara; abaikan menu, loading,
dan iklan; momen 15–60 detik dari pemicu sampai punchline.
MOMEN UTUH: "awal_kejadian" = titik penonton baru paham konteksnya (tiba di lokasi,
misi/aksi dimulai, kalimat niat atau sesumbar Windah), BUKAN di tengah aksi. Mundur
dari pemicu sampai ketemu awal itu, walau lebih dari 20 detik sebelumnya.

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
      "kategori": "ekspektasi_realita | panik | pertama | takjub | lucu | emosional",
      "pemicu": "hh:mm:ss",
      "awal_kejadian": "hh:mm:ss (tiba di lokasi / misi dimulai / kalimat niat)",
      "rekam_mulai": "hh:mm:ss (awal_kejadian - 10 detik)",
      "rekam_selesai": "hh:mm:ss (pemicu + 40 detik)",
      "kutipan": "ucapan Windah persis dari transkrip",
      "dugaan_kejadian": "apa yang kemungkinan terjadi di game (tandai 'dugaan')",
      "punchline": "kalimat/reaksi penutup",
      "hook_ide": ["BARIS 1 / BARIS 2 / BARIS 3", "alternatif"],
      "skor": 1-10,
      "alasan_skor": "",
      "keyakinan_timestamp": "tinggi | sedang | rendah"
    }
  ]
}
Urutkan dari skor tertinggi, maksimal 10 klip per segmen. Jangan mengarang:
bila transkrip tidak jelas, tulis "tidak terbaca" dan turunkan keyakinan.
```
