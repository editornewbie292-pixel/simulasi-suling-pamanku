---
name: klip-windah
description: Editor klip streaming Windah Basudara main GTA VI. Pengguna mengirim rekaman layar potongan stream, Claude menganalisis, bertanya seperlunya (posisi cam, format, momen), lalu merender editan siap posting - format TikTok 9:16 (split gameplay + cam besar, kotak judul hook ungu-pink, glitch, speed lines anime, impact, SFX) atau format kotak (frame stream utuh dengan cam asli di tengah latar hitam, caption punchline statis, punch-in ke wajah). Tanpa voice-over - murni momen. Pakai setiap kali pengguna mengirim rekaman/klip Windah atau GTA VI dan minta diedit, "bikin editan", "edit klip ini", "jadikan tiktok", "bikin versi 1:1/kotak".
---

# klip-windah

Rekaman layar masuk, editan siap posting keluar. `SKILL` = folder file ini. Perintah:

```bash
bash SKILL/scripts/klip-windah analisis VIDEO --transkrip   # info, lembar frame bergrid, usulan cam, puncak suara, transkrip
bash SKILL/scripts/klip-windah pratinjau RENCANA.json       # gambar diam beberapa detik: cek crop SEBELUM render
bash SKILL/scripts/klip-windah render RENCANA.json          # MP4 1080x1920, 30 fps, -14 LUFS
bash SKILL/scripts/klip-windah thumbnail RENCANA.json       # cover 9:16 (bagian "thumbnail" di rencana)
bash SKILL/scripts/klip-windah sfx                          # buat ulang SFX bawaan
```
Butuh `uv` dan `ffmpeg`. Pertama kali, uv memasang paket Python sendiri; transkrip memakai Whisper `small`
(sekitar 480 MB, diunduh dari huggingface.co saat pertama dipakai).

## Aturan program clipper (WAJIB, cek setiap video)
1. **Harus ada gameplay GTA VI + Windah** di klipnya (momen meme, epic, dll. bebas). Video tanpa gameplay
   (mis. hanya avatar/cam bicara) tidak memenuhi syarat - format cerita pun wajib memuat potongan gameplay.
2. **Endcard template 3 detik wajib di akhir setiap video**, utuh: durasi lengkap, pesan jelas, **tanpa efek/filter**
   (tanpa watermark, teks, SFX, atau loudnorm di atasnya). File template disimpan di `assets/endcard/` dan
   otomatis disambung oleh `render`. Bila belum ada, render memberi PERINGATAN: beri tahu pengguna bahwa video
   belum boleh diposting.
3. **Watermark resmi motion klip wajib** (`assets/watermark/motionklip.png`) di bagian klip (bukan di endcard).
4. Opsional: "goreng" jumlah views / peak viewers Windah (sumber: streamcharts) sebagai meme atau jedag-jedug.
   Angka harus dari sumber yang dikirim pengguna (screenshot/link) - jangan mengarang angka. Data yang sudah
   dikirim ada di `assets/data/streamcharts.json` (+ screenshot aslinya); tambahkan entri baru bila pengguna
   mengirim data baru, selalu dengan tanggal. Contoh: 18 Nov 2026 Windah **#1 dunia** peak viewers GTA VI
   (392.505), di atas IShowSpeed (371.840). Selalu sebut tanggal datanya bila dipakai di video.

## Alur kerja (ikuti urutannya)
0. **Mencari bahan**: pengguna memakai AI pencari momen miliknya (berbasis transkrip YouTube). Prompt dan
   cara membaca hasil JSON-nya ada di `prompt/pencari-momen.md`. Claude tidak bisa mengunduh dari YouTube.
1. **Pengguna mengirim rekaman.** Upload ada di `~/.claude/uploads/...`. Salin ke folder kerja
   `hasil-klip/<nama-singkat>/` di repo ini (folder itu di-gitignore), jangan ubah file aslinya.
2. **Analisis**: `analisis VIDEO --transkrip`. Lalu **lihat** `lembar.jpg` (Read): grid kuning menandai
   koordinat piksel sumber setiap 10%. Catat:
   - area stream di dalam rekaman (`stream_box`): buang UI ponsel/browser, taskbar, bar hitam. `area_konten` dari
     cropdetect hanya membuang bar hitam;
   - kotak cam Windah (`cam_box`): mulai dari `cam_usulan[0].usulan_cam_box`, betulkan dengan melihat lembar.
     Bila cam berpindah atau stream ganti ke cam layar penuh di tengah video, catat detiknya;
   - momen: puncak suara (`puncak_suara`) + transkrip = teriakan, tawa, punchline. Untuk detik efek yang pas
     (ledakan, layar WASTED), cari lonjakan warna/beda frame dengan OpenCV, jangan menebak dari lembar.
   - **gangguan rekaman**: notifikasi ponsel, pop-up aplikasi, kursor. Tutup dengan `tutup` (diburamkan).
   - **akhir rekaman**: buang layar hitam/kosong di ujung; akhiri tepat sebelum gambar game hilang.
   - **perfect cut**: bagian yang mengganggu (notifikasi, jeda kosong) lebih baik DIBUANG (`buang`) daripada
     diburamkan. Pilih titik potong di gambar yang diam/sama di kedua sisi (mis. tulisan WASTED tetap di tempat)
     dan cek dengan frame sebelum/sesudah; tanpa transisi atau glitch di sambungan. Bila pengguna menyebut
     rentang kira-kira, cek frame-nya dan geser sedikit bila perlu (sebutkan alasannya).
   - Rekaman layar ponsel sering menyimpan rotasi di metadata: `info.w/h` sudah ukuran tampil; pakai itu.
3. **Tanya pengguna** (AskUserQuestion, maksimal 4 pertanyaan, sertakan apa yang kamu lihat). Yang biasanya perlu:
   - **Format**: TikTok 9:16, kotak, atau keduanya.
   - **Posisi cam** (TikTok): di atas atau di bawah. Pengguna bilang posisinya bervariasi - selalu tanya.
   - **Momen/potongan**: usulkan rentang `potong` (mis. 0:12-0:58) dan sebutkan alasannya.
   - **Judul hook** (TikTok) atau **caption punchline** (kotak): tawarkan 2-3 pilihan.
   Jangan tanya hal yang sudah jelas dari video.
4. **Tulis rencana** `hasil-klip/<nama>/<format>.json` (skema di bawah), jalankan `pratinjau`, **lihat** gambarnya:
   wajah utuh di panel cam, gameplay tidak terpotong aneh, judul tidak menutupi wajah. Betulkan lalu ulangi.
5. **Render**, lalu cek beberapa frame hasil (ffmpeg `-ss T -frames:v 1`) terutama di titik efek.
6. **Thumbnail** bila diminta: isi bagian `thumbnail` di rencana, jalankan `thumbnail`, lihat hasilnya
   (teks tidak menabrak tulisan penting game, wajah + tangan/ekspresi utuh). Gaya bawaan: frame game paling
   dramatis (mis. WASTED) di atas, wajah Windah besar di bawah, teks Anton besar putih ber-outline hitam di atas
   dengan kata kunci kuning (`sorot`), emoji boleh.
7. **Kirim** MP4 ke pengguna dengan SendUserFile, plus ringkasan: durasi, efek di detik berapa, saran judul
   postingan + hashtag. Tawarkan revisi (posisi, judul, efek). **Jangan pernah memposting untuk pengguna.**

## Gaya (dari video referensi pengguna)

### TikTok 9:16 (`"format": "tiktok"`)
- **Split layar**: panel gameplay (default 57% tinggi, `porsi_game`) + panel cam besar (wajah dan bahu memenuhi
  panel). `posisi_cam`: `"bawah"` (seperti referensi) atau `"atas"`. Sambungan tanpa garis.
- **Kotak judul hook** di sambungan, 2-3 detik pertama (`judul_durasi`), lalu hilang: huruf kapital Anton, putih,
  kotak gelap, tepi gradasi ungu ke pink. Pola kalimat referensi:
  "BANG WINDAH BASUDARA JADI ORANG PERTAMA YANG DAPET IKAN DI GTA 6" - sebut Windah, klaim
  superlatif/pertama/rekor atau kejadian lucu, sebut GTA 6, maksimal sekitar 12 kata, 2-3 baris, bahasa gaul.
- **Mulai di tengah aksi** dengan kalimat Windah yang memancing rasa penasaran; durasi sekitar 30-60 detik dengan
  alur: setup -> ketegangan -> puncak -> penutup lucu. Tidak ada caption per kata.
- **Efek**:
  - `glitch` (detik): pecah warna RGB + noise 0,3 detik + SFX glitch. Untuk lompatan/potongan, dan sekali saat
    judul hilang (sekitar `judul_durasi` - 0,2) bila ingin persis referensi.
  - `speedlines` `[[mulai, selesai, "tipis"|"tebal"]]`: garis anime putih dari tepi. **Tipis** sepanjang
    ketegangan (menunggu, mengejar), **tebal** 1,5-2,5 detik di puncak (+ whoosh otomatis 0,35 detik sebelumnya).
  - `impact` (detik): kilat putih + layar bergetar 0,4 detik + boom. Taruh tepat di puncak (teriakan, ledakan,
    "LET'S GO"). Maksimal 1-2 per klip.
  - `cam_penuh` `[[mulai, selesai]]`: potong ke wajah layar penuh untuk reaksi besar (opsional di TikTok).

### Kartu hook + caption per frasa (standar "editan bagus" dari referensi pengguna)
Dipakai di setiap klip kecuali pengguna minta lain. Kriteria pengguna: hook kartu ala thumbnail di 2-3 detik
pertama, kalimat hook bercerita kontras, caption di setiap ucapan, transisi flash/blur, watermark di safe zone.
- `"hook"`: kartu 2-3 detik di depan klip (menggantikan kotak `judul`; jangan pakai keduanya):
  latar frame game diburamkan (`detik_latar`, pilih frame paling dramatis/payoff), **cutout wajah Windah**
  (rembg `u2net_human_seg`, model 176 MB diunduh sekali ke `~/.u2net`) dari `detik_wajah` dengan bingkai putih,
  bawah memudar; teks 3 baris (`teks`, `warna` per baris: putih/merah/kuning/oranye/hijau/pink, `skala` per
  baris, `sorot` {KATA: warna}). Animasi: blur->tajam + punch-zoom, zoom pelan, glitch RGB, flash putih ke klip.
  SFX otomatis (whoosh, boom, glitch, whoosh). `audio_asli: [a, b]` = cuplikan suara asli Windah (detik sumber)
  diputar di bawah kartu, mis. kalimat sesumbarnya. `naik_wajah` (bawaan 0,74) menaikkan wajah bila tertutup teks.
  Pola teks hook: lihat daftar di bawah; jangan hanya "dulu vs sekarang".
- `"caption_frasa": true`: transkrip timeline hasil (Whisper small, waktu per kata) jadi frasa 2-4 kata ke
  `<rencana>_caption.json`, lalu ditampilkan (Anton putih, outline hitam + bayangan) di sisi cam dekat sambungan
  (TikTok) / tepi bawah gambar (kotak). **Selalu baca dan koreksi file caption itu sebelum render final**:
  Whisper sering salah dengar bahasa gaul dan bisa berhalusinasi kata berulang. Bagian yang tidak jelas: hapus,
  jangan menebak. Format: `[[mulai, selesai, "TEKS"], ...]` dalam detik timeline hasil.
- Pola hook: ekspektasi vs realita (NGAKU ___ / ENDINGNYA ___), rekor/pertama, angka (streamcharts), rahasia,
  pertanyaan, reaksi, satu-satunya, peringatan, kegagalan lucu ("13 TAHUN NUNGGU / 5 MENIT LANGSUNG ___"),
  perbandingan. Tawarkan 2-3 pilihan ke pengguna.

### Kotak (`"format": "kotak"`) - "1:1" versi referensi
- Frame stream utuh **dengan cam asli seperti di stream** (normal), diletakkan di tengah latar hitam 9:16.
  Referensi memotong samping ke rasio sekitar 5:4 (`"rasio_kotak": 1.25`); cam asli dijaga tetap kelihatan.
  `null` = 16:9 utuh. Untuk benar-benar persegi pakai `1.0`.
- **Caption punchline statis** sepanjang video (`caption`): kutipan Windah yang paling lucu, huruf kecil, diakhiri
  "..", contoh referensi "salip aelah..". Putih kecil berbayang di tengah gambar (`caption_y` 0-1).
- **Punch-in**: `cam_penuh` ke wajah saat tertawa/bereaksi, 1-3 detik. Boleh `impact` kecil di awal punch-in.
- Pendek: sekitar 10-20 detik, satu lelucon.
- `endcard`: bawaannya file pertama di `assets/endcard/` (wajib, lihat Aturan program). `"endcard": "path"` untuk
  file lain. Jangan pernah membuat sendiri end card yang meniru branding program/merek mana pun.

### Umum
- **Watermark motion klip selalu dipasang** (`assets/watermark/motionklip.png`, banner lebar penuh) di **safe zone**
  TikTok/Reels/Shorts: tidak di 150 px teratas dan tidak di 480 px terbawah (area caption, username, tombol).
  - TikTok: **di sela facecam dan gameplay** (titik tengahnya tepat di sambungan), 68% lebar layar, opacity 0,88 -
    jangan di atas gameplay. Kotak judul otomatis naik/turun ke sisi cam supaya tidak menumpuk.
    Atur dengan `"watermark_lebar"` (piksel) dan `"watermark_opacity"` (0-1) asal tetap terbaca.
  - Kotak: tepat di atas gambar, di latar hitam (judul, bila ada, pindah ke bawah gambar).
  - `"watermark_y"` (titik tengah) untuk memindah, `"watermark": null` untuk mematikan.
- **Emoji** di judul/teks didukung (font Noto Color Emoji sistem; di Windows Segoe UI Emoji).
- **Tanpa voice-over, murni momen.** Suara stream asli dipertahankan, dinormalisasi ke -14 LUFS.
- Watermark sponsor lain dari referensi (mis. Dunia Games) **tidak** ditiru.
- SFX bawaan dibuat sintetis (`sfx/bawaan/`). Bila pengguna mengirim SFX sendiri, simpan sebagai
  `sfx/whoosh.wav`, `sfx/boom.wav`, `sfx/glitch.wav`, `sfx/riser.wav`, `sfx/klik.wav` (mp3/m4a/ogg juga bisa) -
  otomatis dipakai menggantikan bawaan. SFX bebas: `"sfx_tambahan": [["riser", 12.0, 0.8]]` (nama, detik, volume).
  `"volume_sfx"` mengalikan semua SFX; `"tanpa_sfx": true` mematikannya.

## Skema rencana
Semua kotak dalam **piksel video sumber** `[x, y, lebar, tinggi]`; semua detik **relatif terhadap awal `potong`**.
```json
{
  "input": "hasil-klip/ikan/rekaman.mp4",
  "output": "hasil-klip/ikan/tiktok.mp4",
  "format": "tiktok",
  "potong": [12.0, 70.0],
  "stream_box": [0, 140, 1080, 608],
  "cam_box": [820, 520, 260, 228],
  "game_box": null,
  "posisi_cam": "bawah",
  "porsi_game": 0.57,
  "judul": "Bang Windah Basudara jadi orang pertama yang dapet ikan di GTA 6",
  "judul_durasi": 2.5,
  "glitch": [2.3],
  "speedlines": [[27.5, 38.5, "tipis"], [39.5, 41.5, "tebal"]],
  "impact": [39.8],
  "cam_penuh": [],
  "tutup": [[820, 70, 640, 110, 19.5, 23.5]],
  "pratinjau_detik": [1, 30, 40],
  "thumbnail": {
    "output": "hasil-klip/ikan/thumbnail.jpg",
    "detik_game": 40.0, "detik_cam": 41.0,
    "teks": "Perfect landing kali 😂", "sorot": ["KALI"],
    "posisi_cam": "bawah", "posisi_teks": "atas",
    "ukuran_teks": 128, "porsi_game": 0.62, "fokus_cam_y": 0.8
  }
}
```
`buang`: `[[a, b], ...]` rentang yang dihapus, dalam detik **sumber** relatif awal `potong`; semua detik efek
lain (`glitch`, `impact`, `speedlines`, `cam_penuh`, `tutup`) memakai timeline **hasil** setelah dibuang.
`tutup`: `[x, y, w, h, mulai, selesai]` area sumber yang diburamkan. Thumbnail: `fokus_cam_y` 0-1 menggeser wajah
(besar = wajah naik), `fokus_game_x/y`, `zoom_game`, `zoom_cam`.
Kotak: `"format": "kotak"`, `"rasio_kotak": 1.25`, `"caption": "salip aelah.."`, `"cam_penuh": [[9.0, 11.5]]`,
opsional `"endcard": "path/endcard.mp4"`. `game_box` kosong = tengah `stream_box` dengan rasio panel.

## Sebelum pengguna posting
Ingatkan: klip hanya bila ada izin (program clipper resmi Windah atau izin langsung) dan cek ulang judul/caption.
Jangan menaruh spoiler cerita besar GTA VI di judul tanpa peringatan.
