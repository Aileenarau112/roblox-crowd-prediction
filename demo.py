"""Interactive offline demo: python demo.py (no Roblox account needed)."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent/'src'))
import pandas as pd
from data import ROOT, INPUTS
from predict import predict_frame

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--example', action='store_true', help='Run the supplied real examples without prompting.')
    args = parser.parse_args()
    print('\nROBLOX CROWD | Perkiraan tingkat keramaian\n')
    print('Sepi: 0-99 | Sedang: 100-999 | Ramai: 1000+ pemain aktif')
    print('Perkiraan pada snapshot data, bukan ramalan besok.\n')
    if args.example:
        frame = pd.read_csv(ROOT/'examples/games.csv')
    else:
        choice = input('Pilih 1 untuk contoh game, atau 2 untuk input sendiri [1]: ').strip()
        if choice in ('', '1'):
            frame = pd.read_csv(ROOT/'examples/games.csv')
        elif choice == '2':
            prompts = {'visits':'Total kunjungan', 'favorites':'Jumlah favorit',
                       'age_days':'Umur game (hari)', 'max_players':'Kapasitas pemain per server'}
            frame = pd.DataFrame([{key:float(input(prompts[key]+': ')) for key in INPUTS}])
        else:
            raise ValueError('Pilih 1 atau 2.')
    result = predict_frame(frame)
    cols = (['name'] if 'name' in result else [])+['predicted_crowd', 'outside_training_range']
    print(result[cols].to_string(index=False))
    print('\npredicted_crowd = prediksi keramaian; outside_training_range = input di luar rentang data belajar.')
    print('Model bisa salah, terutama untuk game sepi dan sedang yang contohnya sedikit.')

if __name__ == '__main__':
    try:
        main()
    except (ValueError, FileNotFoundError) as exc:
        print(f'Belum dapat memprediksi: {exc}\nPastikan model dibuat dengan python src/train.py.')
        sys.exit(1)
