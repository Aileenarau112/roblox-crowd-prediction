# Roblox Crowd Prediction — aplikasi deployment

Aplikasi Streamlit untuk memperkirakan kategori keramaian game Roblox dari kunjungan, favorit, umur game dan kapasitas satu server. Isi empat angka, lalu klik **Prediksi keramaian**. Contoh game berasal dari data uji snapshot 16 Oktober 2026. Bukan data live atau ramalan pemain besok.

## Menjalankan di Windows

Gunakan Python 3.11 atau 3.12. Buka terminal di folder ini. Jika `.venv` sudah ada dari proyek sebelumnya, lewati perintah pertama.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

Buka alamat lokal pada terminal, biasanya `http://localhost:8501`. Matikan dengan Ctrl+C. Model tepercaya sudah disertakan di `models/crowd_model.joblib`; aplikasi tidak memerlukan pelatihan atau login Roblox.

## Deployment

Ikuti **[DEPLOYMENT.md](DEPLOYMENT.md)**: salin pembaruan ke repository GitHub yang sama, commit dan push, buka https://share.streamlit.io, pilih repository dan branch, isi main file path **`app.py`**, pilih **Python 3.12**, lalu deploy. Tidak ada API key atau secrets yang diperlukan.

Model `.joblib` sekarang sengaja disertakan dan tidak diabaikan `.gitignore`. Model sekitar 1 MB ini harus ikut diunggah. `.venv` tetap tidak diunggah. Versi scikit-learn dipatok **1.5.2** sesuai model. Jangan mengubah hanya versi pustaka tanpa memperbarui model dan evaluasi bersama.

Paket ini disiapkan dan diuji lokal. URL publik baru tersedia setelah deployment dari akun GitHub/Streamlit pemilik repository; belum ada URL publik yang diklaim.

## Fitur aplikasi

- Formulir empat input serta contoh game dari data uji.
- Prediksi sepi (0–99), sedang (100–999), ramai (1.000+ pemain aktif).
- Pembanding pemain sebenarnya pada snapshot untuk contoh bawaan.
- Unduh hasil CSV, halaman evaluasi dan penjelasan keterbatasan.

Batas kategori adalah keputusan proyek, bukan kategori resmi Roblox. Pemain aktif tidak masuk model. Kapasitas satu server bukan total pemain online. Rasio favorit per 1.000 kunjungan dihitung sebagai fitur tambahan; rasio ini bukan retensi pengguna.

## Hasil sesuai versi di laptop pengguna

Random Forest dengan profil lengkap, `min_samples_leaf=2`. Ada 301 game dari 298 kreator; kelas terdiri dari 16 sepi, 35 sedang, 250 ramai. Split: 240 latih, 61 uji, kreator dipisahkan.

| Evaluasi uji | Model | Tebak semua ramai |
|---|---:|---:|
| Akurasi | 83,61% (51/61) | 81,97% (50/61) |
| Macro-F1 | 0,4136 | 0,3003 |
| Recall sepi | 0% (0/2) | 0% |
| Recall sedang | 22,22% (2/9) | 0% |
| Recall ramai | 98% (49/50) | 100% |

CV macro-F1 model terpilih: 0,6330. Model belum andal untuk kelas sepi/sedang; akurasi didominasi kelas ramai. Sampel pelacak game bukan sampel acak seluruh Roblox. Belum ada pengujian lintas hari, game baru sebelum rilis, atau prediksi pendapatan. Hasil tidak membuktikan sebab akibat.

![Matriks kesalahan](results/confusion_matrix.png)

## Reproduksi eksperimen

```powershell
.venv\Scripts\python.exe src/train.py
.venv\Scripts\python.exe src/build_notebook.py
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Pelatihan lengkap berada di src/train.py dan tidak berjalan pada tiap kunjungan aplikasi. Pipeline memilih fitur, log1p, standardisasi dan model. Empat lipatan validasi pada data latih memisahkan kreator; model dipilih dari macro-F1 validasi lalu dievaluasi pada data uji yang disisihkan. Data uji tidak digunakan untuk tuning. Simpangan baku lipatan bukan interval kepercayaan. Versi pustaka di results/environment.json.

Skor lama 85,25% berasal dari lingkungan awal dengan versi scikit-learn berbeda dan tidak dipakai dalam paket deployment ini. Demo terminal masih tersedia melalui `python demo.py`. Prediksi CSV melalui `python src/predict.py examples/games.csv results/example_predictions.csv`.

## Struktur

```text
app.py                         aplikasi Streamlit
requirements.txt               dependensi yang sesuai model
.streamlit/config.toml         tema dan konfigurasi
models/crowd_model.joblib       model untuk deployment
src/                           data, pelatihan, prediksi dan kolektor
data/                          snapshot asli, manifest, data bersih
results/                       audit, skor, grafik, prediksi
notebooks/                     eksplorasi hasil
tests/                         pemeriksaan model dan formulir aplikasi
DEPLOYMENT.md                  langkah unggah dan hosting
```

## Sumber

Daftar ID awal dari [rodict](https://rodict.vercel.app/api-docs); seluruh statistik model diambil ulang melalui [API publik Roblox](https://create.roblox.com/docs/cloud/reference/domains/games) pada 16 Oktober 2026. Dua entri tidak tersedia dikeluarkan. Hash, URL dan waktu respons ada di data/raw/manifest.json. Waktu tersebut adalah penyimpanan respons, bukan waktu pengukuran internal Roblox. Aplikasi tidak mengambil statistik live.

Lisensi MIT mencakup kode proyek, bukan hak atas merek dan konten game. Atribusi data: [data/README.md](data/README.md). Proyek pendidikan independen, tidak berafiliasi dengan Roblox Corporation.