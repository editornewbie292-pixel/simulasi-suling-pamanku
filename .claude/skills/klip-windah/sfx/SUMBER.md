# SFX & backsound pilihan pengguna

File audio TIDAK di-commit: repo ini publik, dan lisensi Pixabay/TikTok melarang menyebarkan file mentahnya.
Sumbernya folder Google Drive pengguna (link-nya juga TIDAK ditulis di repo; ada di env `KLIP_SFX_DRIVE` di
environment cloud pengguna, atau `sfx/drive.local.txt` yang di-gitignore).

**Di awal setiap sesi edit, jalankan dulu:** `bash SKILL/scripts/klip-windah sinkron-sfx`
(tanpa env/link: minta pengguna mengirim link folder Drive SFX-nya, lalu `--folder URL`). File yang sudah
diolah dilewati; `--ulang` mengolah ulang semuanya. Pengguna cukup upload SFX baru ke folder Drive yang sama.

Nama file -> fungsi (lihat `PERAN` di `scripts/sinkron_sfx.py`): nama persis fungsinya (`boom.mp3`,
`boom_2.mp3`) atau kata kunci di nama asli Pixabay:

| Fungsi / keluaran | Kata kunci nama file | Dipakai untuk |
|---|---|---|
| sfx/sting.wav | sting, orchestra-hit | pembuka kartu hook (menggantikan whoosh+boom) |
| sfx/boom.wav | vine-boom, boom, impact | impact / punchline (efek `impact`) |
| sfx/boom_sinematik.wav | cinematic-boom | impact dramatis (`sfx_tambahan`) |
| sfx/whoosh.wav | whoosh, swoosh | SEMUA transisi (potongan/glitch, keluar kartu hook), sebelum speed lines tebal |
| sfx/glitch.wav, sfx/shutter.wav | glitch / shutter, camera | tidak dipakai untuk transisi (pengguna tidak suka); hanya bila diminta |
| sfx/getout.wav | get-out, getout | ENDING lucu: `"get_out": true` - klip dipotong tepat setelah momen sus/lucu/sarkas, frame beku + get out, lalu endcard (permintaan pengguna 21 Nov 2026) |
| sfx/fatality.wav, sfx/awkward_moment.wav, sfx/bonecrack.wav | fatality / awkward / bone-crack | ada di Drive (21 Nov 2026), fungsi belum disepakati - tanya pengguna sebelum dipakai |
| sfx/bruh.wav | bruh | momen gagal/kocak: `"sfx_tambahan": [["bruh", detik, 0.9]]` |
| sfx/klik.wav, riser, scratch | click / riser / scratch | opsional |
| musik/<nama>_loop.wav | musik, music, backsound, bgm, tiktok audio, lofi, phonk | backsound: `"musik": true` |

Pengolahan otomatis: SFX = buang hening awal, ambil bunyi pertama (berhenti di jeda >0,15 dtk), batas durasi per
fungsi, fade out, puncak -2 dBFS. Backsound = HANYA bagian pertama lagu (sampai jeda hening pertama, maks 10 dtk),
loop 1 bar: panjang bar dicari dari kemiripan isi 1,2 dtk (67-150 BPM), lalu awal/panjang dihaluskan agar
sambungan mulus, crossfade 60 ms, 150 dtk, -14 LUFS (permintaan pengguna: loop tanpa sambungan janggal).
File dengan nama asing tidak diolah: tanyakan fungsinya ke pengguna dan minta ganti nama di Drive.

Selera pengguna: SFX dipilih pengguna sendiri; Claude tidak bisa mendengar, jadi jangan memilih/mengganti SFX tanpa
persetujuan. Penempatan disetujui pengguna: orchestra hit = hook, vine boom = impact/punchline, bruh = momen
gagal/kocak. Klip Bigfoot/pesawat/dugem pertama tetap versi lama atas permintaan pengguna.

Status 20 Nov 2026: folder Drive BARU (link di env, bukan di repo) berisi file bernama fungsinya: sting, boom,
bruh, klik, "simple whoosh", cinematic boom, dan backsound (TikTok audio). Shutter sengaja tidak dipakai lagi.
Batas akhir bunyi -60 dB supaya ekor whoosh (0,52 dtk) tidak terpotong.
