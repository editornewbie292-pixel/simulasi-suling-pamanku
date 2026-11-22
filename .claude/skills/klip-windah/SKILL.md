---
name: klip-windah
description: Editor klip streaming Windah Basudara main GTA VI. Pengguna mengirim rekaman layar potongan stream, Claude menganalisis, bertanya seperlunya (posisi cam, format, momen), lalu merender editan siap posting - format TikTok 9:16 (split gameplay + cam besar, kotak judul hook ungu-pink, glitch, speed lines anime, impact, SFX) atau format kotak (frame stream utuh dengan cam asli di tengah latar hitam, caption punchline statis, punch-in ke wajah), plus gaya viral: format banding (Windah vs streamer lain, atas-bawah bersamaan atau berurutan dengan kartu MEANWHILE), bar judul statis, stiker reaksi, caption 1 kata, pencari momen sus. Tanpa voice-over - murni momen. Pakai setiap kali pengguna mengirim rekaman/klip Windah atau GTA VI dan minta diedit, "bikin editan", "edit klip ini", "jadikan tiktok", "bikin versi 1:1/kotak", "bikin perbandingan/perbedaan Windah vs streamer lain", "cari momen sus".
---

# klip-windah

Rekaman layar masuk, editan siap posting keluar. `SKILL` = folder file ini. Perintah:

```bash
bash SKILL/scripts/klip-windah analisis VIDEO --transkrip   # info, lembar frame bergrid, usulan cam, puncak suara, transkrip
bash SKILL/scripts/klip-windah pratinjau RENCANA.json       # gambar diam beberapa detik: cek crop SEBELUM render
bash SKILL/scripts/klip-windah render RENCANA.json          # MP4 1080x1920, 30 fps, -14 LUFS
bash SKILL/scripts/klip-windah thumbnail RENCANA.json       # cover 9:16 (bagian "thumbnail" di rencana)
bash SKILL/scripts/klip-windah sfx                          # buat ulang SFX bawaan
bash SKILL/scripts/klip-windah sinkron RENCANA.json         # format banding: cari detik mulai rekaman streamer lain (suara game)
bash SKILL/scripts/klip-windah cari-sus VIDEO               # kandidat momen sus/sindiran 18+ dari ucapan (-> VIDEO_sus.json)
python3 -I -u SKILL/scripts/pantau_chat.py URL_LIVE --jendela 20 --ambang 6 > hasil-klip/pantau_live/monitor.log
                                                            # pantau lonjakan live chat (YouTube Data API)
```
**Pemantau live chat**: butuh API key YouTube Data API v3 di Network secrets environment (host www.googleapis.com,
header X-Goog-Api-Key, tanpa prefiks). Jalankan di background, pantau `^MOMEN` lewat Monitor (grep --line-buffered,
saring duplikat kata sama <3 menit), kirim notifikasi HP hanya untuk lonjakan kuat. Lonjakan "GG" ratusan orang =
misi/cutscene besar (ikonik); jawaban polling ("boleh", "setuju", warna/rambut) bukan momen; baca `contoh` pesan di
`chat_<id>.jsonl` untuk tahu konteksnya (mis. "L driving", "skill issue" = momen gagal lucu). Chat telat 10-30 dtk.
**Strategi platform** (riset pengguna 22 Nov 2026): TikTok = polos, momen sus & ikonik. YouTube Shorts = cerita ulang
dengan VO pengguna + SFX + meme pekat + kolase hook (Prompt C di `prompt/pencari-momen.md`). Meme: Claude memberi
KEYWORD, pengguna yang mencari & mengunggah ke Drive (jangan mengunduh meme sendiri).
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
4. **Rekaman streamer lain (MiawAug, dll.) DILARANG** oleh aturan motion klip (dikonfirmasi pengguna 22 Nov 2026).
   Format `banding`/`berurutan` hanya boleh memakai rekaman Windah sendiri (mis. dua momen Windah, atau kartu teks
   "STREAMER LAIN KETIKA ..." tanpa footage/nama/foto streamer lain - tanyakan pengguna dulu).
5. Opsional: "goreng" jumlah views / peak viewers Windah (sumber: streamcharts) sebagai meme atau jedag-jedug.
   Angka harus dari sumber yang dikirim pengguna (screenshot/link) - jangan mengarang angka. Data yang sudah
   dikirim ada di `assets/data/streamcharts.json` (+ screenshot aslinya); tambahkan entri baru bila pengguna
   mengirim data baru, selalu dengan tanggal. Contoh: 18 Nov 2026 Windah **#1 dunia** peak viewers GTA VI
   (392.505), di atas IShowSpeed (371.840). Selalu sebut tanggal datanya bila dipakai di video.

## Alur kerja (ikuti urutannya)
- **Cam HD (upscale AI)**: `camhd RENCANA.json` membuat `<rencana>_camhd.mp4` (Real-ESRGAN General x4v3 ONNX,
  4,8 MB dari huggingface.co, dicampur 75% AI + 25% Lanczos = `cam_hd_campur`) di timeline hasil; lalu
  `"cam_hd": true` di rencana. Lambat (~1 dtk/frame; 45 dtk klip = ~22 menit): jalankan di background SETELAH
  `potong`/`buang`/`cam_box` final (berubah = buat ulang). Pengguna menyetujui hasilnya untuk klip Bigfoot.
- **Cari SFX CC0**: `python3 -I SKILL/scripts/cari_sfx.py hasil-klip/pilihan_sfx.html kata1 "kata 2" ...`
  (API Openverse tanpa login, maks 20 hasil per kueri) membuat halaman berpemutar audio untuk DIDENGAR PENGGUNA;
  kirim dengan SendUserFile. Unduhan langsung Freesound diblokir dari container (403), Pixabay diblokir
  Cloudflare - pengguna yang mengunduh pilihannya. Self-host Openverse tidak membantu (indeks saja, filenya tetap
  di Freesound).
- **Transisi**: efek visual glitch tetap boleh, tapi BUNYINYA `sfx_transisi` (bawaan whoosh), bukan shutter/glitch.
- **SFX & backsound dari Drive pengguna**: di awal setiap sesi edit jalankan `klip-windah sinkron-sfx`
  (lihat `sfx/SUMBER.md`). Link Drive TIDAK boleh ditulis di repo (publik).
- **Musik latar**: `"musik": true` (lihat `musik/SUMBER.md`): di bawah kartu hook + klip, ducking otomatis,
  endcard tidak disentuh. Pakai untuk klip baru.
- **SFX**: pakai file pilihan pengguna di `sfx/` (lihat `sfx/SUMBER.md`). Pengguna menilai selera SFX Claude
  jelek - jangan memilih/mengunduh SFX sendiri; minta pengguna yang memilih.
- **Kualitas sumber menentukan HD-nya hasil.** Rekaman layar HP (mis. 1608x720) hanya memuat stream 720p dan cam
  ~270 px yang harus diperbesar ~4x. Render memakai Lanczos + penajaman otomatis, tapi tidak bisa menambah detail.
  Sarankan pengguna merekam dari PC/laptop layar 1080p+ (OBS / Xbox Game Bar Win+G), YouTube 1080p60 layar penuh,
  bitrate tinggi; di HP: layar penuh landscape, kualitas perekam tertinggi.
- **File besar (>30 MB) lewat Google Drive**: pengguna mengirim link folder/file Drive. Daftar file:
  `uvx gdown --folder URL` (cukup untuk membaca ID + nama; unduhan gdown sendiri gagal karena dialihkan ke host
  `doc-*.googleusercontent.com` yang berganti-ganti).
  Simpan unduhan di `hasil-klip/<nama>/` (di-gitignore). Unduh tiap file dengan
  `curl -L -o NAMA "https://drive.usercontent.google.com/download?id=ID&export=download&confirm=t"`.
  Host drive.google.com, drive.usercontent.google.com, docs.google.com sudah diizinkan di environment.
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
   - **SFX transisi** (potongan/glitch & keluar kartu hook): bawaan `whoosh`; tawarkan juga SFX lain yang ada di
     `sfx/` (sebutkan namanya). Pengguna TIDAK suka shutter/glitch di transisi dan akan meminta penyesuaian
     lebih lanjut - selalu tanyakan, jangan dilewati. Simpan jawabannya di `"sfx_transisi"`.
   Pertanyaan lebih dari 4: gabungkan, atau ajukan dua kali. Jangan tanya hal yang sudah jelas dari video.
4. **Tulis rencana** `hasil-klip/<nama>/<format>.json` (skema di bawah), jalankan `pratinjau`, **lihat** gambarnya:
   wajah utuh di panel cam, gameplay tidak terpotong aneh, judul tidak menutupi wajah. Betulkan lalu ulangi.
5. **Render**, lalu cek beberapa frame hasil (ffmpeg `-ss T -frames:v 1`) terutama di titik efek.
6. **Thumbnail** bila diminta: isi bagian `thumbnail` di rencana, jalankan `thumbnail`, lihat hasilnya
   (teks tidak menabrak tulisan penting game, wajah + tangan/ekspresi utuh). Gaya bawaan: frame game paling
   dramatis (mis. WASTED) di atas, wajah Windah besar di bawah, teks Anton besar putih ber-outline hitam di atas
   dengan kata kunci kuning (`sorot`), emoji boleh.
7. **Kirim** versi `*_upload.mp4` (otomatis dibuat render: 1080x1920, maks 4,5 Mbps, ~20-30 MB) dengan
   SendUserFile `display: "attach"` - file besar (50-90 MB) sulit disimpan pengguna ke galeri HP.
   Beri nama jelas, mis. `1_Windah_Bigfoot_GTA6.mp4` (`"output_upload"` di rencana). Kirim MP4 ke pengguna dengan SendUserFile, plus ringkasan: durasi, efek di detik berapa, saran judul
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
  - `impact` (detik): kilat putih + layar bergetar 0,4 detik + boom. `"sfx_impact": "fatality"` mengganti boom-nya. Taruh tepat di puncak (teriakan, ledakan,
    "LET'S GO"). Maksimal 1-2 per klip.
  - `get_out`: `true` / `{"sfx": "getout", "volume": 1.0}` - ending meme: akhiri `potong` TEPAT setelah momen
    sus/lucu/sarkas; suara asli + musik langsung dipotong, SFX get out diputar utuh sementara VIDEO TETAP
    MENGALIR (lanjutan rekaman tanpa efek; jangan freeze - pengguna tidak mau; `"hitam": true` = layar hitam), lalu endcard. Variasi `"beku": {"detik": <detik SUMBER absolut>,
    "box": [x,y,w,h], "waktu_zoom": 0.3}`: frame beku + punch-zoom ke kotak (mis. kerusakan depan mobil paling
    parah) sinkron dengan get out - dipakai bila pengguna minta "frame beku lalu zoom". Pakai untuk klip yang berakhir dengan punchline (permintaan pengguna).
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
  **Wajib 2 gambar** (permintaan pengguna): Windah + 1 elemen pendukung dari game lewat `"elemen"`:
  `{"detik": t, "box": [x,y,w,h], "gaya": "cutout"|"kartu", "model": "isnet-general-use" (objek/makhluk) |
  "u2net_human_seg" (orang/NPC), "lebar": px, "x": 0-1, "naik": 0-1, "miring": derajat, "ambang": 0-255}`.
  Cutout untuk objek yang kontras (Bigfoot, NPC); `kartu` (foto berbingkai miring) untuk yang sulit dipotong
  (asap, langit, pesawat kecil - perketat box ke objeknya). Latar kartu hook jangan adegan yang sama dengan
  elemen (objek jadi menyatu); pilih ekspresi wajah Windah paling hidup (cek 3-4 frame cam). Pratinjau cepat:
  `klip-windah hook RENCANA.json` -> `<rencana>_hook.jpg`.
- `"caption_frasa": true`: transkrip timeline hasil (Whisper small, waktu per kata) jadi frasa 2-4 kata ke
  `<rencana>_caption.json`, lalu ditampilkan (Anton putih, outline hitam + bayangan) di sisi cam dekat sambungan
  (TikTok) / tepi bawah gambar (kotak). **Selalu baca dan koreksi file caption itu sebelum render final**:
  Whisper sering salah dengar bahasa gaul dan bisa berhalusinasi kata berulang. Bagian yang tidak jelas: hapus,
  jangan menebak. Format: `[[mulai, selesai, "TEKS"], ...]` dalam detik timeline hasil.
  Bila hasil otomatis tipis/aneh, transkrip ulang sumber dengan dan tanpa VAD lalu bandingkan (kalimat yang
  muncul di kedua versi = paling bisa dipercaya). `language="id"` membuat dialog NPC berbahasa Inggris ikut
  "diterjemahkan" ngawur - jangan jadikan caption, kecuali ucapan Windah sendiri ("What? Bigfoot?").
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
- **Tanpa voice-over, murni momen** (analisis video viral 21 Nov 2026 juga: tanpa VO). Suara stream asli dipertahankan, dinormalisasi ke -14 LUFS.
- Watermark sponsor lain dari referensi (mis. Dunia Games) **tidak** ditiru.
- SFX bawaan dibuat sintetis (`sfx/bawaan/`). Bila pengguna mengirim SFX sendiri, simpan sebagai
  `sfx/whoosh.wav`, `sfx/boom.wav`, `sfx/glitch.wav`, `sfx/riser.wav`, `sfx/klik.wav` (mp3/m4a/ogg juga bisa) -
  otomatis dipakai menggantikan bawaan. SFX bebas: `"sfx_tambahan": [["riser", 12.0, 0.8]]` (nama, detik, volume).
  `"volume_sfx"` mengalikan semua SFX; `"tanpa_sfx": true` mematikannya.

## Gaya viral (analisis 5 video >100 rb views, 21 Nov 2026) - dipakai bila pengguna memintanya secara spesifik
Temuan: KONSEP > efek. Tanpa VO, tanpa kartu hook animasi; bar judul statis yang menjanjikan konflik; 35-60 dtk;
momen SPESIFIK yang kontras (topik umum "TOP 5", "ADA LAGU INDO" flop). Pola: perbandingan dengan streamer lain
(video 2,1 jt = banding + sus), sus 18+ sindiran, ironi/sarkas, drama/curhat. Prompt AI pencari momen v2:
`prompt/pencari-momen.md` (Prompt A kandidat, Prompt B adegan sama di VOD streamer lain).
- **Banding bersamaan** (`"format": "banding"`, gaya video 2,1 jt): dua rekaman atas-bawah, adegan sama berjalan
  bersamaan, label "NAMA :" kiri atas tiap panel. `"kanvas": "1:1"` (bawaan, 1080x1080) atau `"9:16"`.
  `sumber[0]` = panel atas (streamer lain), `sumber[1]` = bawah (Windah) - urutan referensi. `sumber[0].potong`
  menentukan durasi; `sumber[1].mulai` = detik mulai B (jalankan `sinkron` - korelasi suara game, tulis hasil +
  keyakinan ke rencana; `"geser"` untuk koreksi manual). `"audio"`: `"campur"` (bawaan) / `"atas"` / `"bawah"` /
  `[[mulai, selesai, "atas"|"bawah"|"campur"], ...]` (gantian, mis. suara lawan dulu lalu Windah); `volume` per sumber.
- **Banding berurutan** (`"format": "berurutan"`, gaya "YOUTUBER LAIN KETIKA LANDING"): `bagian` = daftar
  `{"input", "potong", "stream_box", "label"?, "fokus_x"?}` atau kartu `{"kartu": "MEANWHILE", "sub": "in our universe",
  "durasi": 2.5, "sfx": "nama"?}` (latar hitam; bar judul disembunyikan). Streamer lain ±3 dtk/orang -> MEANWHILE ->
  Windah -> punchline (WASTED/get out).
- **Rekaman streamer lain DILARANG program motion klip** (lihat Aturan program no. 4): jangan merender banding dengan
  footage streamer lain; pakai untuk Windah-vs-Windah (mis. ekspektasi vs realita dua momen) saja.
- **Bar judul** (`"bar_judul": "TEKS"`, semua format): bar putih selebar layar sepanjang video, pengganti kartu hook.
  `"bar_gaya": "hitam"` (teks hitam tebal, bawaan) / `"outline"` (putih outline hitam); `bar_ukuran`, `bar_y`.
  Kotak: bar tepat di atas gambar, watermark pindah ke bawah gambar. Gaya polos = `kotak` + `"rasio_kotak": null` +
  `bar_judul`, tanpa hook/speedlines/impact/musik.
- **Stiker reaksi** (gaya "melongo"): `"stiker": [[mulai, selesai, "melongo"], ...]` atau objek
  `{"mulai", "selesai", "teks", "lebar": 0.5, "x": 0.5, "y": 0-1?, "zoom": 1.35, "fokus_y": 0.42, "ukuran": 64}` -
  wajah Windah dari `cam_box` diperbesar berbingkai putih + teks reaksi. Butuh `cam_box`.
- **Caption 1 kata** (gaya akun4): `"caption_mode": "kata"` - tiap frasa caption tampil sebagai 1 kata kunci
  berwarna bergantian (`"caption_warna": ["kuning", "putih", "hijau"]`). Koreksi kata kasar di file caption.
- **Momen sus**: `cari-sus VIDEO` memindai ucapan (kata sus + reaksi Windah) -> kandidat + `usul_potong`. Harus
  SINDIRAN, bukan eksplisit: render memberi PERINGATAN bila judul/bar/label/caption memuat kata eksplisit
  (`KATA_EKSPLISIT`) - ganti sebelum posting. Ending yang cocok: `get_out`.
- `get_out` di format banding: video mengalir (lanjutan kedua panel/bagian terakhir) atau `"hitam": true`.

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
`zoom`: `[[mulai, selesai, x, y, w, h], ...]` punch-in panel game (TikTok) / gambar (kotak) ke area sumber -
untuk kejadian di pinggir layar yang terpotong crop tengah (mis. pesawat jatuh di langit kanan atas). Hindari
area cam asli di dalam kotak zoom. Lacak posisi objeknya dulu dengan crop frame per 0,5 detik.
`tutup`: `[x, y, w, h, mulai, selesai]` area sumber yang diburamkan. Thumbnail: `fokus_cam_y` 0-1 menggeser wajah
(besar = wajah naik), `fokus_game_x/y`, `zoom_game`, `zoom_cam`.
Kotak: `"format": "kotak"`, `"rasio_kotak": 1.25`, `"caption": "salip aelah.."`, `"cam_penuh": [[9.0, 11.5]]`,
opsional `"endcard": "path/endcard.mp4"`. `game_box` kosong = tengah `stream_box` dengan rasio panel.

## Sebelum pengguna posting
Ingatkan: klip hanya bila ada izin (program clipper resmi Windah atau izin langsung) dan cek ulang judul/caption.
Jangan menaruh spoiler cerita besar GTA VI di judul tanpa peringatan.
