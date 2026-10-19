# Kenali proyekmu dulu

Nama proyek: **Roblox Crowd Prediction — Prediksi Tingkat Keramaian Game Roblox**.

## Penjelasan satu menit

Saya ingin mengetahui apakah jumlah kunjungan, favorit, umur game, dan kapasitas server bisa membantu memperkirakan seberapa ramai sebuah game Roblox. Saya mengambil contoh game yang jumlah pemain aktifnya sudah diketahui. Model belajar dari sebagian game, lalu diuji pada game lain dari kreator berbeda.

Jawaban model adalah salah satu dari tiga kategori: sepi, sedang, atau ramai. Ini tugas **klasifikasi**, karena jawabannya berupa kategori.

## Contoh yang mudah dibayangkan

Sebuah game memiliki jutaan kunjungan sepanjang masa. Angka itu tidak otomatis berarti banyak orang masih bermain sekarang. Kita ingin melihat apakah komputer dapat mempelajari perbedaan itu dari statistik beberapa game.

Kita memberi model empat angka: kunjungan, favorit, umur dalam hari, kapasitas satu server. Kita **tidak memberikan jumlah pemain aktif**, karena itulah informasi yang hendak ditebak. Pemain aktif aslinya hanya dipakai untuk mengecek tebakan.

## Apa yang dilakukan tiap tahap?

| Tahap | Artinya |
|---|---|
| Dataset | Kumpulan contoh game beserta statistik dan jawabannya |
| Pembersihan | Membuang entri tidak tersedia dan menolak angka yang tidak masuk aturan data |
| EDA | Melihat distribusi serta pola pada contoh belajar melalui grafik |
| Feature engineering | Membuat rasio favorit per 1.000 kunjungan dari dua angka yang tersedia |
| Training | Model mempelajari pola pada 240 game |
| Validasi | Membandingkan pilihan model memakai bagian data belajar yang bergantian |
| Testing | Memeriksa model terpilih pada 61 game yang disisihkan |
| Prediksi | Memasukkan statistik game untuk mendapatkan perkiraan kategorinya |

## Mengapa tidak cukup melihat akurasi?

Dari 61 game uji, 50 termasuk ramai. Jadi, tanpa belajar apa pun, menebak semua game ramai sudah benar sekitar 82%. Namun tebakan itu selalu salah untuk game sepi dan sedang.

Model benar untuk 51 game: 0 sepi, 2 sedang, dan 49 ramai. Model belum berhasil mengenali dua contoh sepi dan masih lemah pada game sedang. Hasil ini perlu disebut dengan jujur.

## Cara mencoba di Windows

1. Ekstrak ZIP proyek.
2. Buka terminal di folder yang berisi README.md dan demo.py.
3. Jalankan empat perintah pada bagian "Menjalankan proyek" di README.
4. Pilih contoh game untuk percobaan pertama. Setelah paham, masukkan angka sendiri.

Total kunjungan bukan pemain unik. Kapasitas server juga bukan jumlah pemain aktif seluruh game. Tidak perlu login ke Roblox.

## Memperbarui GitHub dan deployment

Gunakan repository yang sudah ada: https://github.com/Aileenarau112/roblox-crowd-prediction. Ikuti DEPLOYMENT.md untuk menyalin perubahan, commit, push, lalu hosting. Model models/crowd_model.joblib harus ikut diunggah pada tahap deployment ini. Jangan mengunggah .venv atau secrets.

## Kalimat untuk menjelaskan ke dosen

“Proyek saya memperkirakan kategori keramaian game Roblox dari empat statistik game. Saya membandingkan beberapa model dan memilihnya berdasarkan validasi data latih. Pada 61 game uji, Random Forest benar untuk 51 game, tetapi kemampuan mengenali game sepi dan sedang masih terbatas karena datanya sedikit.”

Jangan menyebut proyek ini sebagai ramalan game viral, prediksi pemain besok, bot Roblox, atau pembuat game. Itu bukan yang diuji.
