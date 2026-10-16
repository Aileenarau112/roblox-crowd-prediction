"""Predict a CSV without current-player counts: python src/predict.py input.csv output.csv."""
import argparse
import joblib
import pandas as pd
from data import ROOT, build_features

def predict_frame(frame):
    bundle = joblib.load(ROOT/'models/crowd_model.joblib')
    features = build_features(frame)
    result = frame.copy()
    result['predicted_crowd'] = bundle['model'].predict(features)
    ranges = bundle['training_ranges']
    result['outside_training_range'] = [
        any(row[c] < limits['min'] or row[c] > limits['max'] for c,limits in ranges.items())
        for _,row in features.iterrows()
    ]
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input_csv')
    parser.add_argument('output_csv')
    args = parser.parse_args()
    try:
        result = predict_frame(pd.read_csv(args.input_csv))
    except (ValueError, FileNotFoundError) as exc:
        parser.exit(1, str(exc)+'\nJalankan python src/train.py jika model belum tersedia.\n')
    result.to_csv(args.output_csv, index=False)
    print(result.to_string(index=False))

if __name__ == '__main__':
    main()
