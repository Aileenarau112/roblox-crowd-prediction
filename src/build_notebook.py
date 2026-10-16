"""Build and execute the companion notebook's Python cells without a notebook server."""
import contextlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    cells = []
    state = {}
    count = 0
    def markdown(source):
        cells.append({'cell_type':'markdown','id':f'cell-{len(cells):03}','metadata':{},'source':source.splitlines(keepends=True)})
    def code(source):
        nonlocal count
        count += 1
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exec(compile(source, '<notebook-cell>', 'exec'), state)
        cells.append({'cell_type':'code','id':f'cell-{len(cells):03}','metadata':{},'source':source.splitlines(keepends=True),
                      'execution_count':count,'outputs':[{'output_type':'stream','name':'stdout','text':output.getvalue().splitlines(keepends=True)}]})

    markdown('# Roblox Crowd Prediction\n\n**Pertanyaan:** apakah kunjungan sepanjang masa cukup untuk memperkirakan keramaian saat snapshot diambil?\n\nNotebook ini membaca dataset dan hasil eksperimen yang disertakan. Pelatihan lengkap dijalankan terpisah dengan `python src/train.py`. Sel Python di notebook ini sudah dijalankan saat paket dibuat. Tidak diperlukan akun Roblox.')
    code("from pathlib import Path\nimport json\nimport pandas as pd\ncandidates = [Path.cwd(), Path.cwd().parent, Path.cwd() / 'roblox-crowd']\nROOT = next(p for p in candidates if (p / 'src/train.py').exists())\ngames = pd.read_csv(ROOT / 'data/processed/games.csv')\ntrain = games.loc[games['split'].eq('train')].copy()\ntest = games.loc[games['split'].eq('test')].copy()\nprint('Total:', len(games), '| Belajar:', len(train), '| Uji:', len(test))")
    markdown('## 1. Apa isi satu baris?\n\nSatu baris adalah satu game pada waktu pengambilan. Nama dan ID hanya keterangan. `playing` merupakan jawaban asli; model tidak menerimanya sebagai input.')
    code("columns = ['name', 'visits', 'favorites', 'age_days', 'max_players', 'playing', 'crowd_level']\nprint(train[columns].head(5).to_string(index=False))\nprint('\\nNilai kosong pada input:')\nprint(train[['visits', 'favorites', 'age_days', 'max_players']].isna().sum().to_string())")
    markdown('## 2. EDA dari data belajar\n\nLabel: sepi untuk 0–99 pemain, sedang untuk 100–999, ramai untuk 1.000+. Batas ini merupakan keputusan eksperimen, bukan standar Roblox.\n\n![Distribusi dan hubungan kunjungan dengan pemain](../results/training_eda.png)\n\nSetiap titik pada panel kanan adalah satu game latih. Sumbu logaritmik merapatkan hitungan yang rentangnya sangat besar. Titik dengan kunjungan besar tidak selalu berada di kelas ramai.')
    code("print('Distribusi label pada data latih:')\nprint(train['crowd_level'].value_counts().to_string())\nprint('\\nRingkasan statistik data latih:')\nprint(train[['visits', 'favorites', 'age_days', 'max_players']].describe().round(2).to_string())")
    markdown('## 3. Pastikan kreator terpisah\n\nGame dari kreator yang sama dapat memiliki karakteristik mirip. Kita mengelompokkan berdasarkan jenis dan ID kreator, lalu memisahkannya antara belajar dan uji. ID kreator sendiri tidak menjadi fitur.')
    code("overlap = set(train['creator_group']) & set(test['creator_group'])\nassert not overlap\nprint('Jumlah kreator yang muncul di kedua bagian:', len(overlap))\nprint('Empat lipatan validasi di dalam data latih:')\nprint(pd.read_json(ROOT / 'results/cv_folds.json').to_string(index=False))")
    markdown('## 4. Bagaimana fitur disiapkan?\n\nDua kelompok fitur dibandingkan: kunjungan+umur, serta profil lengkap dengan favorit, kapasitas server dan rasio favorit per 1.000 kunjungan. Fitur deterministik dihitung tanpa memakai label. `log1p` dan standardisasi berada dalam Pipeline model; standardisasi dipelajari pada setiap lipatan data latih.')
    code("sample = train[['visits','favorites','age_days','max_players']].head(3).copy()\nsample['favorites_per_1000_visits'] = 1000 * sample['favorites'] / sample['visits'].clip(lower=1)\nassert 'playing' not in sample.columns\nprint(sample.round(3).to_string(index=False))")
    markdown('## 5. Model mana yang dipilih?\n\nTabel ini berasal dari validasi data latih, bukan data uji. Angka tertinggi memilih kombinasi fitur dan model. Macro-F1 memberi bobot sama pada ketiga kategori; akurasi saja didominasi game ramai.')
    code("scores = pd.read_csv(ROOT / 'results/cv_results.csv')\nprint(scores[['feature_set','model','cv_macro_f1','cv_std','cv_accuracy']].round(4).to_string(index=False))")
    markdown('## 6. Evaluasi akhir\n\nModel terpilih diuji setelah seluruh pemilihan selesai. Tebakan semua ramai merupakan pembanding yang ditetapkan sejak awal.\n\n![Matriks kesalahan pada data uji](../results/confusion_matrix.png)\n\nBaris adalah kelas asli, kolom adalah prediksi. Angka pada diagonal adalah prediksi benar.')
    code("metrics = json.loads((ROOT / 'results/test_metrics.json').read_text(encoding='utf-8'))\nreport = metrics['test_report']\nbaseline = metrics['majority_test_report']\nprint('Model:', metrics['selected_model'], '| Fitur:', metrics['feature_set'])\nprint('Accuracy model:', round(report['accuracy'], 4), '| pembanding:', round(baseline['accuracy'], 4))\nprint('Macro-F1 model:', round(report['macro avg']['f1-score'], 4), '| pembanding:', round(baseline['macro avg']['f1-score'], 4))\nfor label in ['sepi','sedang','ramai']:\n    print(label, '| recall:', round(report[label]['recall'], 4), '| jumlah contoh:', int(report[label]['support']))\nerrors = pd.read_csv(ROOT / 'results/errors.csv')\nprint('\\nSemua kesalahan uji:')\nprint(errors[['name','playing','crowd_level','prediction']].to_string(index=False))")
    markdown('## 7. Kesimpulan yang dapat dipertanggungjawabkan\n\nModel belajar lebih banyak daripada sekadar menebak kelas mayoritas, tetapi belum andal pada kelas kecil. Empat contoh sepi di data uji terlalu sedikit untuk kesimpulan luas. Profil lengkap mendapat CV macro-F1 lebih tinggi daripada kunjungan+umur pada eksperimen ini; tidak ada klaim sebab akibat.\n\nData merupakan katalog game yang dilacak, bukan seluruh Roblox. Snapshot ini tidak menguji ramalan besok atau game yang belum dirilis. Setelah melihat kesalahan uji, jangan menyetel model lalu tetap menyebut data yang sama sebagai evaluasi independen.\n\n**Latihan memahami:** mengapa 81,97% dari menebak semua ramai belum cukup? Mengapa kapasitas satu server tidak sama dengan total pemain aktif? Mengapa kita menyimpan data uji sejak awal?')
    destination = ROOT/'notebooks/01_memahami_keramaian.ipynb'
    destination.parent.mkdir(exist_ok=True)
    notebook = {'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.12'}},'nbformat':4,'nbformat_minor':5}
    destination.write_text(json.dumps(notebook, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'Notebook built; {count} Python cells executed successfully.')

if __name__ == '__main__':
    main()
