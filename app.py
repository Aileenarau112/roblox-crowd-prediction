"""Browser app: python -m streamlit run app.py."""
from pathlib import Path
import sys
import json
import importlib.metadata
import joblib
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'src'))
from data import INPUTS, build_features

st.set_page_config(page_title='Roblox Crowd | Prediksi keramaian', page_icon='🎮', layout='wide')

@st.cache_resource
def load_model():
    environment = json.loads((ROOT/'results/environment.json').read_text(encoding='utf-8'))
    if importlib.metadata.version('scikit-learn') != environment['scikit-learn']:
        raise ValueError('Versi model dan pustaka tidak sesuai. Gunakan requirements.txt dari paket deployment.')
    return joblib.load(ROOT/'models/crowd_model.joblib')

@st.cache_data
def examples():
    return pd.read_csv(ROOT/'data/processed/games.csv')

@st.cache_data
def metrics():
    return json.loads((ROOT/'results/test_metrics.json').read_text(encoding='utf-8'))

try:
    bundle = load_model()
except (ValueError, FileNotFoundError) as error:
    st.error(str(error))
    st.info('Pastikan model dan results/environment.json ikut diunggah, serta dependensi dipasang dari requirements.txt.')
    st.stop()

with st.sidebar:
    st.title('🎮 Roblox Crowd')
    st.caption('Dari statistik game menjadi perkiraan keramaian.')
    st.markdown('**Kategori proyek**\n\n🟦 Sepi · 0–99 pemain\n\n🟨 Sedang · 100–999 pemain\n\n🟩 Ramai · 1.000+ pemain')
    st.divider()
    st.caption('Kategori buatan proyek, bukan kategori resmi Roblox. Data snapshot: 16 Oktober 2026.')
    st.markdown('[Sumber statistik Roblox](https://create.roblox.com/docs/cloud/reference/domains/games)')

st.title('Seberapa ramai game Roblox ini?')
st.write('Masukkan statistik game atau coba contoh dari dataset. Model memperkirakan kategori pemain aktif pada kondisi snapshot.')
st.info('Ini demonstrasi tugas machine learning. Bukan data live atau ramalan jumlah pemain besok. Model masih lemah untuk game sepi dan sedang.')
predict_tab, evaluation_tab, about_tab = st.tabs(['Coba prediksi', 'Hasil pengujian', 'Tentang proyek'])

with predict_tab:
    mode = st.radio('Sumber input', ['Isi sendiri', 'Contoh game'], horizontal=True)
    sample = None
    data = examples()
    if mode == 'Contoh game':
        # Held-out games only: examples do not reuse observations used in training.
        choices = data.loc[data['split'].eq('test')].copy()
        choices['display'] = choices['name']+' · '+choices['universe_id'].astype(str)
        selected = st.selectbox('Pilih game dari data uji', choices['display'].tolist())
        sample = choices.loc[choices.display.eq(selected)].iloc[0]
        st.caption('Statistik contoh berasal dari 16 Oktober 2026 dan dapat berbeda dari keadaan game sekarang.')
    defaults = {'visits':1000000, 'favorites':20000, 'age_days':365., 'max_players':20}
    if sample is not None:
        defaults = {column: float(sample[column]) if column=='age_days' else int(sample[column]) for column in INPUTS}
    with st.form('prediction_form'):
        left, right = st.columns(2)
        with left:
            visits = st.number_input('Total kunjungan', min_value=0, max_value=10**15, value=int(defaults['visits']), step=1000, help='Total visits, bukan pemain yang sedang online.')
            favorites = st.number_input('Jumlah favorit', min_value=0, max_value=10**15, value=int(defaults['favorites']), step=100)
        with right:
            age = st.number_input('Umur game (hari)', min_value=0., max_value=100000., value=float(defaults['age_days']), step=1.)
            capacity = st.number_input('Kapasitas satu server', min_value=1, max_value=1000000, value=int(defaults['max_players']), step=1, help='Max Players / Server Size. Bukan pemain aktif seluruh game.')
        submitted = st.form_submit_button('Prediksi keramaian', type='primary')
    if submitted:
        frame = pd.DataFrame([{'visits':visits,'favorites':favorites,'age_days':age,'max_players':capacity}])
        try:
            features = build_features(frame)
            prediction = str(bundle['model'].predict(features)[0])
            descriptions = {'sepi':'0–99 pemain aktif', 'sedang':'100–999 pemain aktif', 'ramai':'1.000 atau lebih pemain aktif'}
            st.subheader(f'Perkiraan: {prediction.upper()}')
            st.write(descriptions[prediction])
            outside = [column for column,limits in bundle['training_ranges'].items() if frame.iloc[0][column]<limits['min'] or frame.iloc[0][column]>limits['max']]
            if outside:
                st.warning('Sebagian angka berada di luar rentang data belajar. Perkiraan untuk input ini makin tidak pasti.')
            st.caption('Hasil merupakan tebakan model dan dapat salah. Masuk dalam rentang data belajar tidak menjamin prediksi benar.')
            if sample is not None:
                st.write(f"Pembanding snapshot: **{int(sample['playing']):,} pemain aktif**, kategori **{sample['crowd_level']}**.")
                st.caption('Angka pemain aktif ini hanya ditampilkan sebagai pembanding setelah prediksi; tidak dimasukkan ke model.')
            result = frame.assign(predicted_crowd=prediction)
            st.download_button('Unduh hasil CSV', result.to_csv(index=False).encode('utf-8'), 'prediksi_roblox.csv','text/csv')
        except ValueError as error:
            st.error(str(error))

with evaluation_tab:
    score = metrics()
    report = score['test_report']
    baseline = score['majority_test_report']
    a,b,c = st.columns(3)
    a.metric('Akurasi data uji', f"{report['accuracy']*100:.2f}%")
    b.metric('Macro-F1', f"{report['macro avg']['f1-score']:.4f}")
    c.metric('Akurasi tebak semua ramai', f"{baseline['accuracy']*100:.2f}%")
    st.write('Model dipilih melalui validasi data latih, lalu diuji pada 61 game dari kreator yang dipisahkan. Model terpilih: Random Forest, profil lengkap.')
    labels = ['sepi','sedang','ramai']
    table = pd.DataFrame([{'Kategori':label,'Contoh uji':int(report[label]['support']),'Recall':f"{report[label]['recall']*100:.2f}%"} for label in labels])
    st.dataframe(table, hide_index=True, use_container_width=True)
    st.warning('Pada pengujian ini model belum berhasil mengenali dua game sepi dan hanya mengenali dua dari sembilan game sedang. Akurasi didominasi kelas ramai; jangan memakai aplikasi sebagai dasar keputusan penting.')
    st.image(str(ROOT/'results/confusion_matrix.png'), caption='Baris: kategori sebenarnya. Kolom: prediksi model.')

with about_tab:
    st.markdown('''### Apa yang dipelajari model?
Model memakai kunjungan, favorit, umur game, kapasitas server, dan rasio favorit per 1.000 kunjungan. Jumlah pemain aktif tidak menjadi input.

### Dari mana datanya?
Daftar awal universe ID berasal dari rodict, lalu statistik diambil ulang langsung dari API publik Roblox. Ada 301 game setelah dua entri tidak tersedia dikeluarkan. Data berasal dari satu snapshot, bukan sampel acak seluruh Roblox.

### Alur proyek
Data → audit → pemisahan kreator → fitur → validasi silang → model → evaluasi → aplikasi ini.

### Batas penggunaan
Belum diuji lintas hari, perangkat pengambilan, atau game yang belum dirilis. Kunjungan bukan pemain unik dan favorit bukan retensi. Aplikasi tidak terhubung ke akun Roblox dan tidak mengambil statistik live.

Proyek pendidikan independen, tidak berafiliasi dengan Roblox Corporation.''')
