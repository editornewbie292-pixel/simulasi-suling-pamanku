---
name: klip-windah
description: Editor klip streaming Windah Basudara main GTA VI. Pengguna mengirim rekaman layar potongan stream, Claude menganalisis, bertanya seperlunya (posisi cam, format, momen), lalu merender editan siap posting - format TikTok 9:16 (split gameplay + cam besar, kotak judul hook ungu-pink, glitch, speed lines anime, impact, SFX) atau format kotak (frame stream utuh dengan cam asli di tengah latar hitam, caption punchline statis, punch-in ke wajah). Tanpa voice-over - murni momen. Pakai setiap kali pengguna mengirim rekaman/klip Windah atau GTA VI dan minta diedit, atau hanya mengirim LINK Google Drive/YouTube (mode otomatis: cari momen, potong, edit sendiri tanpa bertanya), "bikin editan", "edit klip ini", "jadikan tiktok", "bikin versi 1:1/kotak".
---

# klip-windah

Rekaman layar masuk, editan siap posting keluar. `SKILL` = folder file ini. Perintah:

```bash
bash SKILL/scripts/cari-momen URL [FOLDER] [--top 15]     # pindai SELURUH live/VOD -> kandidat momen (lihat "Cari momen di live panjang")
bash SKILL/scripts/ambil-link URL [FOLDER] [MULAI-SELESAI] # unduh link YouTube (yt-dlp) / Google Drive (lihat Mode otomatis)
python -I SKILL/scripts/kata_waktu.py LIVE.vtt MULAI SELESAI # waktu PER KATA (subtitle YouTube) -> titik potong rapi
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

## Mode otomatis: pengguna hanya mengirim LINK (permintaan pengguna 26 Nov 2026)
Bila pesan pengguna berisi link (Google Drive / YouTube) tanpa instruksi lain, kerjakan SENDIRI sampai jadi:
cari momen menarik -> potong -> edit sesuai gaya skill ini -> kirim. **Jangan tanya apa pun sebelum render**
(langkah 3 "Tanya pengguna" dilewati); semua pilihan diputuskan Claude lalu disebutkan di ringkasan agar
pengguna bisa minta revisi. Tetap tanya HANYA bila buntu (tidak ada gameplay GTA VI/Windah, file rusak).

1. **Ambil**: `bash SKILL/scripts/ambil-link URL` (cetak path file hasil unduhan; folder Drive = semua video).
   - Drive: file/folder harus dibagikan "Siapa saja yang memiliki link". Gagal HTML = minta pengguna ubah akses.
   - **YouTube** (cara utama pengguna): skrip mengunduh dengan `yt-dlp` (maks 1080p, mp4). Ini **berhasil di
     laptop pengguna** (sesi Claude Code yang berjalan di LAPTOP-914DTFLG, folder `P:\klip-windah`, lewat
     Remote Control; yt-dlp, ffmpeg, uv sudah terpasang di sana). Cek channel resmi Windah (judul/uploader).
     - Link ber-timestamp (`&t=4980s`, `?t=1h23m`) -> otomatis bagian t-30 s.d. t+90 detik.
     - VOD > 30 menit / live tanpa timestamp -> kode 3. Jalankan `cari-momen URL` (bagian "Cari momen di live
       panjang" di bawah), beri pengguna daftar kandidat, lalu unduh bagian pilihannya:
       `ambil-link URL '' 1:23:00-1:26:00`. Ini satu-satunya titik "tanya" di mode otomatis (pilihan pengguna
       27 Nov 2026). Alternatif: pengguna menyebut menitnya sendiri / prompt `prompt/pencari-momen.md`.
     - **Di server cloud diblokir** ("Sign in to confirm you're not a bot") -> kode 2 + info video via YouTube
       Data API. Jangan mengakalinya (cookie, ganti player client, proxy); sarankan menjalankan sesi di laptop
       pengguna (Claude app -> Code -> sesi baru -> LAPTOP-914DTFLG / klip-windah).
     - Unduh hanya video yang boleh diklip (program clipper resmi Windah / channel pengguna sendiri).
2. **Analisis**: `analisis VIDEO --transkrip`, lihat `lembar.jpg`, tentukan `stream_box`, `cam_box`, gangguan.
3. **Pilih momen sendiri** (15-60 dtk, TikTok; video < 75 dtk = pakai hampir utuh): beri skor kandidat dari
   transkrip + `puncak_suara` + lonjakan beda frame memakai prioritas di `prompt/pencari-momen.md`
   (ekspektasi vs realita > panik/teriak > pertama/rekor > takjub > lucu > emosional). Potong dari
   setup/sesumbar sampai punchline + 1-2 dtk reaksi; buang jeda kosong (`buang`) - `analisis` memberi
   `usul_buang_jeda` (sunyi >= 1,5 dtk, relatif rekaman): cek frame-nya, masukkan yang aman ke `buang`, dan
   sebutkan di ringkasan. Rekaman berisi beberapa momen
   kuat = buat maks 3 klip terpisah (`1_...`, `2_...`).
   - **Momen UTUH, mulai dari AWAL kejadian** (permintaan pengguna 27 Nov 2026): penonton yang tidak menonton
     stream harus langsung paham konteksnya - apa yang sedang dilakukan dan kenapa. Contoh: klip rampok bank mulai
     saat tiba/masuk bank (atau kalimat niatnya, mis. "next target", "gua gak PD rampok bank"), BUKAN di depan
     brankas. Cari titik awal dengan mundur dari puncak sampai ketemu pemicunya (tiba di lokasi, misi dimulai,
     kalimat niat/sesumbar), lalu cek frame-nya. Bila jadi > 60 dtk, PADATKAN bagian tengah dengan `buang`
     (jalan kaki, menunggu, menu, diam) - jangan memotong awal atau akhirnya. Sebutkan titik awal + alasannya
     di ringkasan.
4. **Default keputusan** (tanpa tanya): format `tiktok`; `posisi_cam` = sisi yang membuat wajah terlihat paling
   utuh di pratinjau (bawaan `"bawah"`); `hook` kartu + `"caption_frasa": true` (koreksi file caption!);
   1 `impact` di puncak, `speedlines` tipis saat ketegangan + tebal di puncak, `glitch` di sambungan `buang`;
   teks hook = pilihan terkuat dari pola hook; SFX hanya dari `sfx/` pengguna atau bawaan (jangan memilih dari
   `aset/`); tanpa musik/LUT kecuali pengguna pernah memintanya untuk klip ini; tanpa `camhd` (lambat).
5. **Pratinjau -> betulkan -> render -> cek frame** seperti alur biasa (wajib, jangan dilewati).
6. **Kirim** `*_upload.mp4` + ringkasan: rentang sumber yang dipakai dan alasannya, posisi cam, teks hook +
   2 alternatif, efek di detik berapa, saran judul postingan + hashtag. Tawarkan revisi dan versi kotak/camhd.

## Cari momen di live panjang (`cari-momen`, ide dari Clips Kitty, dipilih pengguna 27 Nov 2026)
**WAJIB baca `prompt/prinsip-momen-fyp.md` sebelum memilih momen (cari-momen) dan sebelum menyusun `buang`**:
pilih dari layar + reaksi (bukan transkrip), mulai dari persiapan, simpan pembuktian, klip punchline 10-30 dtk vs
klip misi 1-3 menit, skor kandidat 7 kolom (§7), dan lima tes sebelum render (§8).
Untuk live/VOD Windah utuh (berjam-jam) tanpa menit yang disebut. Unduhannya ringan: audio kualitas rendah,
subtitle otomatis `id`, chat replay (live 5 jam ~ 10-30 menit unduh, jalankan di background), info JSON (heatmap).
Hasil di `hasil-klip/cari-<id>/`: `kandidat.json` + `timeline.txt`.
1. **Sinyal per detik, relatif video itu sendiri (persentil)**: audio (lonjakan dB vs median 30 dtk + kepadatan
   onset = tawa/teriak) 45%, chat (ledakan penulis unik vs 45 dtk sebelumnya, digeser 6 dtk karena chat telat)
   40%, heatmap "paling sering diputar" 15% (bobot dibagi ulang bila chat/heatmap tidak ada). Kelas chat:
   lucu (wkwk, KEKW, ngakak, kocak, 😂), epic (GG, gila, anjir, POG, keren), gagal (F, L, rip, 💀), sus (🤨, sus,
   sensor, astagfirullah), minta klip (clip, klip, jadiin short). Ubah di `KELAS_CHAT` di `cari_momen.py`.
2. **Dua kolam kandidat** (Claude = juri, tanpa AI lain): (a) puncak sinyal di `kandidat.json` (transkrip 90 dtk
   sebelum s.d. 30 dtk sesudah puncak + contoh chat), dan (b) momen yang Claude temukan sendiri dari
   `timeline.txt` (transkrip per menit bertanda `[SUARA]`, `[CHAT xN kelas]`, `[*]`) walau sinyalnya biasa -
   ucapan kuat + sinyal kecil tetap bisa bagus. Subtitle otomatis sering salah dengar: nilai maknanya, bukan ejaan.
3. **Skor 0-100 per kandidat**: prioritas pola #windahGTAVI (memori `pola-klip-windahgtavi`: kebiasaan Windah
   kebongkar > sus/cewek > fail/tragedi lucu > bug > rekor/komunitas > mobil > nyindir), dinaikkan oleh sinyal
   (teriak, chat meledak, kelas chat yang cocok). Energi tinggi tanpa isi (teriak di menu, chat spam) = skor rendah.
   Wajib ada gameplay GTA VI; momen di menu/loading/ngobrol saja dibuang.
4. **Rerank**: bandingkan 8-12 teratas SATU SAMA LAIN (mana yang lebih mungkin ramai), bukan skor absolut saja.
5. **Tandai ⚠️** (jangan dibuang): adegan 18+/sensor, umpatan berat, spoiler cerita besar. Pengguna memutuskan.
6. **Kirim ke pengguna 5-10 kandidat**: waktu SELALU ditulis lengkap "jam 3 menit 26 detik 40" selain
   format 3:26:40 (pengguna 27 Nov 2026 salah baca "3:26" sebagai menit 3), menit awal-akhir (MOMEN UTUH: mundur ke awal kejadian), kategori, skor,
   alasan 1 kalimat, sinyal pendukung (mis. "chat lucu x5, suara +11 dB"), tanda ⚠️. Setelah pengguna memilih:
   `ambil-link URL '' MULAI-SELESAI` (beri buffer ±20 dtk), lalu alur biasa (analisis -> cek visual di lembar
   + beda frame -> rencana -> render). Visual seluruh live TIDAK dianalisis (laptop RAM 7,6 GB) - hanya sekitar
   kandidat terpilih. Simpan daftar juga sebagai `hasil-klip/cari-<id>/daftar_klip.md` dan kirim (SendUserFile).
7. **Unduhan dipakai ulang**: folder `cari-<id>` (audio, chat, vtt) jangan diunduh dua kali; chat replay yang
   masih `.part` sudah bisa dibaca (baris JSON terakhir terpotong dilewati) - pakai untuk daftar awal, lalu pindai
   ulang saat chat lengkap dan perbarui daftarnya. Kuota: audio ±100 MB, chat 5 jam ±185 MB, bagian video 1080p60
   ±45 MB/menit (unduhan per bagian lambat: ±2-3 menit per menit video). Semua lewat internet LAPTOP.

## Alur klip dari live panjang (dipakai dan disetujui pengguna 27 Nov 2026, live #12)
Urutan yang berhasil: `cari-momen` -> daftar kandidat -> pengguna memilih nomor -> **ajukan pertanyaan edit**
(pengguna minta "beri saya pertanyaan" sebelum edit; tulis bernomor dengan pilihan a/b/c + saran, karena pengguna
sering lewat Remote Control di HP dan kotak AskUserQuestion bisa tidak tampil) -> unduh semua bagian sekaligus di
background (`ambil-link URL FOLDER/tmp_N MULAI-SELESAI`, buffer ±20 dtk, lalu ganti nama `N_nama.mp4`) -> kerjakan
klip yang sudah terunduh sambil menunggu yang lain -> kirim semua SEKALIGUS di akhir (pilihan pengguna).
0. **Audio terpotong** (27 Nov 2026: bagian salto audionya 90,7/110 dtk -> akhir klip sunyi, pengguna komplain):
   `ambil-link` sekarang otomatis menambal lewat `scripts/perbaiki_audio.py` (unduh ulang audio saja ±15 dtk,
   selaraskan dengan korelasi silang, mux `-c:v copy`, cadangan `*_audiopotong.mp4`). JANGAN buang stderr
   `ambil-link` (`2>&1 | tail -1` menyembunyikan peringatannya) - baca semua keluarannya, dan sebelum edit cek
   `ffprobe` durasi video vs audio tiap bagian. Setelah render, cek tidak ada detik sunyi (< -60 dB) di bagian
   klip (endcard template memang hening di 1-2 dtk terakhir - abaikan).
1. **Titik potong dari kata**: `kata_waktu.py live.id.vtt MULAI SELESAI` (MULAI = awal bagian yang diunduh, jadi
   detiknya sama dengan file bagian). Pilih kalimat setup -> aksi -> punchline; potong di jeda antar-kalimat
   (mis. keep 11.3-16.0 = satu kalimat utuh). Pengguna: "yang diem/gak penting dalam alur cut aja, tapi cutnya
   harus rapi"; durasi menyesuaikan (hasil 28-62 dtk).
2. **Cek visual tiap bagian**: lembar frame per 3-5 dtk (cerahkan dulu, rekaman malam gelap) + frame resolusi
   penuh di sekitar puncak. Puncak aksi (tembakan, tabrakan) cari dengan puncak dB audio per 0,1 dtk lalu cek
   frame. Buang menu/peta/loading kecuali memberi konteks (peta target bank boleh 1-2 dtk).
3. **Rencana**: `buang` berisi semua yang bukan bagian keep (hitung timeline hasil untuk `impact`/`tutup`).
   1 `impact` di puncak. Format pilihan pengguna: kotak 5:4 + `judul_putih` (lihat Gaya Kotak).
4. **Sensor 18+** (pengguna: "langsung sensor", gaya mosaik, SEMUA yang terbuka termasuk NPC berbikini di latar):
   `"tutup_gaya": "mosaik"`, `"mosaik_px": 36`, kotak `tutup` per sudut kamera (koordinat dari frame bergrid,
   ingat crop kotak 5:4 hanya menampilkan x ±570-1920 bila cam di kanan). Adegan ketelanjangan penuh
   (mis. syuting film dewasa di misi pool boy) DIBUANG total, bukan dimosaik. Kata kasar dibiarkan.
5. **Render**: `render` mendekode seluruh rentang `potong` (60 fps), jadi bagian 7 menit = ±10-15 menit render;
   render paralel boleh tapi saling memperlambat. Cek frame hasil (awal, impact, tengah, akhir + endcard).

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
- **Musik latar**: `"musik": {"file": "musik/latar_tiktok1_loop.wav", "volume_db": -15}` (lihat
  `musik/SUMBER.md`): di bawah kartu hook + klip, ducking otomatis, endcard tidak disentuh. Pakai untuk klip baru.
- **SFX**: pakai file pilihan pengguna di `sfx/` (lihat `sfx/SUMBER.md`). Pengguna menilai selera SFX Claude
  jelek - jangan memilih/mengunduh SFX sendiri; minta pengguna yang memilih.
- **Pustaka aset repo (`aset/` di akar repo, ter-commit, lihat `aset/LISENSI.md`)**: 40 SFX + 9 BGM CC0,
  9 paket audio Kenney CC0, 5 LUT (CC BY 4.0). Path di rencana relatif `aset/`, ekstensi boleh dihilangkan.
  - **Katalog untuk DIDENGAR PENGGUNA**: `python3 -I SKILL/scripts/katalog_aset.py hasil-klip/katalog_sfx.html`
    (bawaan: sfx + Kenney impact/interface/digital) dan `... hasil-klip/katalog_bgm.html bgm/mp3 kenney-cc0/music-jingles`;
    kirim dengan SendUserFile. Tetap pengguna yang memilih - jangan memilih SFX/BGM dari `aset/` sendiri.
  - `"sfx_pilihan": {"boom": "sfx/impact_deep", "whoosh": "...", "glitch": "...", "sting": "..."}` mengganti slot
    SFX otomatis untuk video ini (mengalahkan `sfx/` dan bawaan; `sting` mengaktifkan pembuka kartu hook).
  - `"sfx_tambahan": [["sfx/pop_bubble", 3.2, 0.8]]` - nama boleh langsung path aset.
  - `"musik": {"file": "bgm/bgm_upbeat_vlog", "volume_db": -15}` - BGM CC0, diloop otomatis, aman Content ID
    (lebih aman daripada audio TikTok).
  - `"lut": "lut/slay-04-film"`, `"lut_kekuatan": 0.7` (0-1) - warna gameplay + cam saja (kartu hook, teks,
    watermark, endcard tidak terkena). **Wajib kredit "LUT by slay"** di caption/deskripsi postingan - ingatkan pengguna.
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
   cara membaca hasil JSON-nya ada di `prompt/pencari-momen.md`. Di laptop pengguna Claude bisa memindai sendiri dengan `cari-momen`.
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
- **Mulai dari awal kejadian** (bukan di tengah aksi) supaya penonton paham konteksnya; bagian awal boleh
  langsung dibuka dengan kalimat Windah yang memancing rasa penasaran. Durasi sekitar 30-60 detik dengan
  alur: setup -> ketegangan -> puncak -> penutup lucu; padatkan bagian tengah dengan `buang`. Tidak ada caption per kata.
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
- **Panel judul putih** (pilihan pengguna 27 Nov 2026, "1:1 dengan atasnya ada tempat judul putih"):
  `"judul_putih": "Ngaku skill rampok luar biasa, endingnya cuma dapet 13.000 💀"` = panel putih selebar layar
  tepat DI ATAS gambar, teks hitam Anton rata tengah (maks 3 baris, emoji boleh), sepanjang klip (endcard tidak).
  `"judul_putih_ukuran"` (bawaan 60). Pola kalimat: kontras sesumbar/niat vs hasil, 8-12 kata, gaul, 1 emoji
  (😭/💀). Watermark tetap di dalam frame atas (`watermark_y` 586, `watermark_lebar` 520).
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
`zoom`: `[[mulai, selesai, x, y, w, h], ...]` punch-in panel game (TikTok) / gambar (kotak) ke area sumber -
untuk kejadian di pinggir layar yang terpotong crop tengah (mis. pesawat jatuh di langit kanan atas). Hindari
area cam asli di dalam kotak zoom. Lacak posisi objeknya dulu dengan crop frame per 0,5 detik.
`tutup`: `[x, y, w, h, mulai, selesai(, "blur"|"mosaik")]` area sumber yang disensor; `"tutup_gaya"` = bawaan
semua entri (`"blur"`), `"mosaik_px"` = besar kotak mosaik dalam piksel sumber (bawaan 28). Thumbnail: `fokus_cam_y` 0-1 menggeser wajah
(besar = wajah naik), `fokus_game_x/y`, `zoom_game`, `zoom_cam`.
Kotak: `"format": "kotak"`, `"rasio_kotak": 1.25`, `"judul_putih": "..."`, `"caption": "salip aelah.."`, `"cam_penuh": [[9.0, 11.5]]`,
opsional `"endcard": "path/endcard.mp4"`. `game_box` kosong = tengah `stream_box` dengan rasio panel.

## Sebelum pengguna posting
Ingatkan: klip hanya bila ada izin (program clipper resmi Windah atau izin langsung) dan cek ulang judul/caption.
Jangan menaruh spoiler cerita besar GTA VI di judul tanpa peringatan.
