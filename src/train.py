"""Reproduce the experiment offline: python src/train.py."""
import importlib.metadata
import json
import platform
import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedGroupKFold, GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay, make_scorer, f1_score
from data import ROOT, INPUTS, LABELS, FEATURE_SETS, build_features, load_snapshot

OUT = ROOT/'results'

def save_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')

def main():
    OUT.mkdir(exist_ok=True)
    (ROOT/'models').mkdir(exist_ok=True)
    (ROOT/'data/processed').mkdir(exist_ok=True)
    data, excluded, manifest = load_snapshot()
    if len(data) < 100 or data.crowd_level.value_counts().min() < 10:
        raise ValueError('Data terlalu sedikit untuk rancangan evaluasi ini; tinjau dataset.')
    X, y, groups = build_features(data), data.crowd_level, data.creator_group
    outer = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    train, test = next(outer.split(X, y, groups))
    if set(y.iloc[train]) != set(LABELS) or set(y.iloc[test]) != set(LABELS):
        raise ValueError('Split tidak memuat seluruh kelas; tinjau rancangan sebelum evaluasi.')
    assert set(groups.iloc[train]).isdisjoint(set(groups.iloc[test]))
    data['split'] = 'train'
    data.loc[test, 'split'] = 'test'
    data.to_csv(ROOT/'data/processed/games.csv', index=False)
    audit = {
        'catalog_ids': manifest['requested_universes'], 'verified_ids': manifest['returned_universes'],
        'usable_rows': len(data), 'excluded': excluded,
        'missing_inputs': int(data[INPUTS].isna().sum().sum()),
        'duplicate_ids': int(data.universe_id.duplicated().sum()),
        'creators': int(groups.nunique()), 'train_rows': len(train), 'test_rows': len(test),
        'class_counts': data.crowd_level.value_counts().to_dict(),
        'train_class_counts': y.iloc[train].value_counts().to_dict(),
        'test_class_counts': y.iloc[test].value_counts().to_dict(),
        'observation_start_utc': data.observed_at_utc.min(), 'observation_end_utc': data.observed_at_utc.max(),
        'creator_overlap': 0, 'thresholds': {'sepi': '0–99', 'sedang': '100–999', 'ramai': '1000+'},
    }
    save_json(OUT/'audit.json', audit)
    data.iloc[train][INPUTS+['playing']].describe().to_csv(OUT/'training_summary.csv')
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))
    colors = ['#6b859c', '#d7a337', '#29877d']
    counts = y.iloc[train].value_counts().reindex(LABELS, fill_value=0)
    axes[0].bar(LABELS, counts, color=colors)
    axes[0].set(ylabel='Jumlah game latih', title='Sampel tidak seimbang')
    for label, color in zip(LABELS, colors):
        subset = data.iloc[train].loc[y.iloc[train].eq(label)]
        axes[1].scatter(np.log10(1+subset.visits), np.log10(1+subset.playing), label=label, color=color, alpha=.75, s=22)
    axes[1].axhline(np.log10(100), color='gray', lw=.7, ls='--')
    axes[1].axhline(np.log10(1000), color='gray', lw=.7, ls='--')
    axes[1].set(xlabel='log10(1 + total kunjungan)', ylabel='log10(1 + pemain aktif)', title='Kunjungan besar belum tentu ramai')
    axes[1].legend()
    fig.tight_layout(); fig.savefig(OUT/'training_eda.png', dpi=170); plt.close(fig)
    inner = StratifiedGroupKFold(n_splits=4, shuffle=True, random_state=42)
    folds = list(inner.split(X.iloc[train], y.iloc[train], groups.iloc[train]))
    fold_audit = []
    for i, (a,b) in enumerate(folds):
        assert set(groups.iloc[train].iloc[a]).isdisjoint(set(groups.iloc[train].iloc[b]))
        if set(y.iloc[train].iloc[a]) != set(LABELS) or set(y.iloc[train].iloc[b]) != set(LABELS):
            raise ValueError('Kelas hilang pada lipatan validasi; tinjau desain.')
        fold_audit.append({'fold': i+1, 'train': len(a), 'validation': len(b), 'creator_overlap': 0})
    save_json(OUT/'cv_folds.json', fold_audit)
    metric = make_scorer(f1_score, average='macro', labels=LABELS, zero_division=0)
    candidates = [
        ('mayoritas', DummyClassifier(strategy='most_frequent'), {}),
        ('logistic_regression', LogisticRegression(class_weight='balanced', max_iter=3000), {'model__C': [.1,1,10]}),
        ('decision_tree', DecisionTreeClassifier(class_weight='balanced', random_state=42), {'model__max_depth': [2,4,6], 'model__min_samples_leaf': [3,8]}),
        ('random_forest', RandomForestClassifier(n_estimators=200, class_weight='balanced', random_state=42, n_jobs=1), {'model__max_depth': [None,8], 'model__min_samples_leaf': [2,5]}),
    ]
    fitted, results = {}, []
    for feature_set, cols in FEATURE_SETS.items():
        for name, estimator, grid in candidates:
            pipeline = Pipeline([
                ('select', ColumnTransformer([('numeric', 'passthrough', cols)], remainder='drop')),
                ('log', FunctionTransformer(np.log1p, feature_names_out='one-to-one')),
                ('scale', StandardScaler()), ('model', estimator),
            ])
            search = GridSearchCV(pipeline, grid, scoring={'macro_f1':metric, 'accuracy':'accuracy'}, refit='macro_f1', cv=folds, n_jobs=1, error_score='raise')
            search.fit(X.iloc[train], y.iloc[train])
            index = search.best_index_
            results.append({'feature_set': feature_set, 'model': name,
                            'cv_macro_f1': float(search.best_score_),
                            'cv_std': float(search.cv_results_['std_test_macro_f1'][index]),
                            'cv_accuracy': float(search.cv_results_['mean_test_accuracy'][index]),
                            'best_parameters': json.dumps(search.best_params_)})
            fitted[(feature_set,name)] = search.best_estimator_
            print(feature_set, name, round(search.best_score_,4), flush=True)
    scores = pd.DataFrame(results).sort_values('cv_macro_f1', ascending=False, kind='stable')
    scores.to_csv(OUT/'cv_results.csv', index=False)
    best = scores.iloc[0]
    model = fitted[(best.feature_set, best.model)]
    pred = model.predict(X.iloc[test])
    dummy = fitted[('riwayat_kunjungan','mayoritas')].predict(X.iloc[test])
    report = classification_report(y.iloc[test], pred, labels=LABELS, output_dict=True, zero_division=0)
    metrics = {'selected_model': best.model, 'feature_set': best.feature_set,
               'cv_macro_f1': float(best.cv_macro_f1), 'parameters': json.loads(best.best_parameters),
               'test_report': report, 'label_order': LABELS,
               'confusion_matrix': confusion_matrix(y.iloc[test], pred, labels=LABELS).tolist(),
               'majority_test_report': classification_report(y.iloc[test], dummy, labels=LABELS, output_dict=True, zero_division=0)}
    save_json(OUT/'test_metrics.json', metrics)
    predictions = data.iloc[test].copy()
    predictions['prediction'] = pred
    predictions['correct'] = predictions.crowd_level.eq(predictions.prediction)
    predictions.to_csv(OUT/'test_predictions.csv', index=False)
    predictions.loc[~predictions.correct].to_csv(OUT/'errors.csv', index=False)
    ConfusionMatrixDisplay.from_predictions(y.iloc[test], pred, labels=LABELS, cmap='GnBu', colorbar=False)
    plt.title('Data uji: kreator terpisah'); plt.tight_layout(); plt.savefig(OUT/'confusion_matrix.png', dpi=170); plt.close()
    bundle = {'model': model, 'inputs': INPUTS, 'feature_set': best.feature_set, 'labels': LABELS,
              'training_ranges': {c: {'min':float(X.iloc[train][c].min()), 'max':float(X.iloc[train][c].max())} for c in INPUTS}}
    joblib.dump(bundle, ROOT/'models/crowd_model.joblib')
    restored = joblib.load(ROOT/'models/crowd_model.joblib')
    assert np.array_equal(restored['model'].predict(X.iloc[test]), pred)
    versions = {p:importlib.metadata.version(p) for p in ['numpy','pandas','scikit-learn','scipy','matplotlib','joblib']}
    versions['python'] = platform.python_version()
    save_json(OUT/'environment.json', versions)
    (ROOT/'examples').mkdir(exist_ok=True)
    # Real, held-out examples: inputs intentionally omit the answer (playing).
    chosen = predictions.groupby('crowd_level', sort=False).head(2)
    chosen[['name']+INPUTS].to_csv(ROOT/'examples/games.csv', index=False)
    print(json.dumps(metrics, indent=2), flush=True)

if __name__ == '__main__':
    main()
