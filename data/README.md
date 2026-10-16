# Dataset snapshot Roblox

## Asal

Daftar 303 universe ID diperoleh dari `https://rodict.vercel.app/api/export/games?format=json`. rodict hanya dipakai sebagai daftar awal. Data tersebut bukan sampel acak seluruh game Roblox, dan ekspornya dibatasi maksimum 1.000 game.

Statistik pelatihan diambil ulang lewat `https://games.roblox.com/v1/games?universeIds=...` pada 16 Oktober 2026. Terdapat 301 game tersedia dan dua respons pengganti untuk game yang tidak tersedia (`id=0`, judul tidak tersedia); entri pengganti tidak dipakai. ID yang tidak berhasil dikembalikan dicatat di manifest. Pendapatan perkiraan rodict, rating/rasio turunan yang tidak diverifikasi, serta status dan puncak pemain tidak dipakai sebagai fitur.

Tujuh respons JSON asli, katalog awal, waktu penyimpanan respons dan SHA-256 disimpan di raw/. Waktu pengambilan memakai UTC; tambahkan tujuh jam untuk WIB. JSON disimpan tanpa mengubah isinya. `src/fetch_data.py` menghasilkan ulang manifest dari berkas yang sudah di-cache atau mengambil berkas yang belum tersedia. Proses pelatihan tidak membuat permintaan jaringan.

## Data bersih

`processed/games.csv` dibuat oleh `src/train.py`:

| Kolom | Peran |
|---|---|
| universe_id, root_place_id, name | Identitas dan keterangan; bukan fitur |
| creator_group | Jenis kreator + ID; hanya untuk pemisahan kelompok |
| genre | Keterangan dari respons Roblox; bukan fitur model saat ini |
| visits, favorites | Input hitungan kumulatif |
| age_days | Input umur, dihitung dari waktu penyimpanan respons dikurangi created |
| max_players | Input kapasitas satu server |
| playing | Pemain aktif snapshot; pembentuk target, bukan input |
| observed_at_utc | Waktu respons disimpan, bukan waktu internal Roblox |
| crowd_level | Target sepi/sedang/ramai |
| split | train atau test |

`favorites_per_1000_visits` dibuat secara deterministik ketika pelatihan/prediksi, bukan kolom asli Roblox. Tidak ada imputasi nilai kosong; entri yang gagal validasi dicatat dan dikeluarkan. Aturan kelas tetap: <100 sepi, 100–999 sedang, ≥1000 ramai.

## Atribusi

Sumber statistik: [Roblox Games API](https://create.roblox.com/docs/cloud/reference/domains/games). Sumber daftar ID: [rodict](https://rodict.vercel.app/api-docs). Berikan kredit kepada keduanya saat memakai data ini. Data bukan dataset resmi yang diterbitkan dengan lisensi MIT; lisensi MIT repository hanya berlaku untuk kode buatan proyek. Nama game, deskripsi dalam respons sumber, dan merek tetap milik pemilik masing-masing. Proyek ini tidak berafiliasi dengan Roblox.
