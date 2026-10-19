# Dari proyek lokal menjadi tautan aplikasi

## 1. Perbarui folder repository

Ekstrak ZIP deployment di tempat terpisah. Salin isinya ke folder repository Roblox yang sudah kamu buka di VS Code. Izinkan penggantian file proyek yang sama. Pertahankan `.git` dan `.venv` milikmu; jangan menghapusnya. Simpan salinan perubahan pribadi sebelum mengganti file.

Jalankan:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

Coba input manual, contoh game dan halaman evaluasi. Model sudah disertakan, jadi tidak perlu train ulang untuk mencoba aplikasi. Terminal perlu tetap berjalan saat mencoba aplikasi lokal.

## 2. Commit dan push dari VS Code

Buka Source Control, periksa perubahan, stage, commit dengan pesan `Add Streamlit deployment app`, lalu Push/Sync Changes. Gunakan repository tugas yang sama.

Pastikan `models/crowd_model.joblib` ikut terlihat. Berbeda dengan tahap terminal sebelumnya, model ini **harus diunggah**. `.gitignore` paket sudah diperbarui. Jika aturan lama masih mengabaikannya:

```powershell
git add -f models/crowd_model.joblib
```

Jangan unggah `.venv`, `__pycache__`, atau secrets. Pastikan di GitHub terlihat app.py, requirements.txt, models/, src/, data/ dan results/.

## 3. Deploy

1. Buka https://share.streamlit.io dan login/hubungkan akun GitHub milikmu. Otorisasi dilakukan pemilik akun; tidak perlu mengirim password ke chat.
2. Pilih **Create app**, kemudian **Yup, I have an app** jika ditanyakan.
3. Pilih repository **Aileenarau112/roblox-crowd-prediction** dan branch yang baru kamu push, biasanya `main`.
4. Isi **Main file path: `app.py`**. Jika proyek berada di subfolder, sesuaikan, misalnya `roblox-crowd-prediction/app.py`.
5. Buka **Advanced settings**, pilih **Python 3.12**. Kosongkan Secrets karena aplikasi tidak memerlukannya.
6. Simpan pengaturan dan deploy. Tunggu status berhasil serta halaman tampil. Salin URL yang benar-benar diberikan layanan.

Panduan resmi: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy

## 4. Periksa sebelum mengumpulkan

Buka URL dari jendela browser lain. Coba prediksi manual dan contoh, unduh CSV, serta halaman evaluasi. Pastikan tidak ada traceback. Sesuaikan pengaturan berbagi agar dosen dapat membuka aplikasi. Tambahkan URL yang sudah berhasil diuji ke README GitHub dengan label “Demo aplikasi”. Kumpulkan tautan GitHub dan aplikasi; screenshot lokal saja belum membuktikan deployment.

## Jika ada error

- **ModuleNotFoundError:** pastikan requirements.txt ikut di-push pada lokasi yang dipakai aplikasi.
- **Model tidak ditemukan:** pastikan models/crowd_model.joblib benar-benar terlihat di GitHub.
- **Versi model berbeda:** gunakan scikit-learn 1.5.2 dari paket. Jika mengubah eksperimen, unggah ulang model, results/ dan environment.json bersama.
- **File app tidak ditemukan:** periksa path dan huruf besar/kecil di repository.

## Pembaruan berikutnya

Edit → uji lokal → commit → push ke branch hosting → tunggu pembaruan → periksa kembali URL. Jangan mengganti model saja tanpa hasil dan dependensi yang sesuai. Perubahan Python berbeda dari perubahan requirements; ikuti dokumentasi pengelolaan versi layanan.
