"""Checks for label boundaries, leakage, data splits and persisted predictions."""
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score
from data import ROOT, LABELS, build_features, crowd_label
from predict import predict_frame

class Contracts(unittest.TestCase):
    def test_class_boundaries(self):
        self.assertEqual([crowd_label(v) for v in [0,99,100,999,1000]], ['sepi','sepi','sedang','sedang','ramai'])

    def test_target_never_enters_features(self):
        original = pd.DataFrame([{'visits':1000,'favorites':30,'age_days':100,'max_players':20,'playing':1}])
        changed = original.copy()
        changed['playing'] = 999999
        pd.testing.assert_frame_equal(build_features(original), build_features(changed))

    def test_bad_inputs_rejected(self):
        valid = {'visits':1000,'favorites':30,'age_days':100,'max_players':20}
        for column,value in [('visits',-1),('favorites',float('inf')),('age_days',None),('max_players',0),('max_players',1.5)]:
            with self.subTest(column=column):
                with self.assertRaises((ValueError,TypeError)):
                    build_features(pd.DataFrame([{**valid,column:value}]))

    def test_creator_disjoint_and_metrics_reproducible(self):
        games = pd.read_csv(ROOT/'data/processed/games.csv')
        train = games.loc[games.split.eq('train')]
        test = games.loc[games.split.eq('test')]
        self.assertTrue(set(train.creator_group).isdisjoint(set(test.creator_group)))
        self.assertFalse(games.universe_id.duplicated().any())
        predicted = predict_frame(test)
        saved = pd.read_csv(ROOT/'results/test_predictions.csv')
        np.testing.assert_array_equal(predicted.predicted_crowd, saved.prediction)
        metrics = json.loads((ROOT/'results/test_metrics.json').read_text())
        actual = f1_score(test.crowd_level, predicted.predicted_crowd, labels=LABELS, average='macro', zero_division=0)
        self.assertAlmostEqual(actual, metrics['test_report']['macro avg']['f1-score'])

if __name__ == '__main__':
    unittest.main()
