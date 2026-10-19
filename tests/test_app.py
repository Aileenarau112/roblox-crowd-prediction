from pathlib import Path
import unittest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]

class AppContracts(unittest.TestCase):
    def test_manual_prediction_and_example(self):
        app = AppTest.from_file(str(ROOT/'app.py'), default_timeout=60).run()
        self.assertEqual(len(app.exception), 0)
        app.button[0].click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any('Perkiraan:' in item.value for item in app.subheader))
        app.radio[0].set_value('Contoh game').run()
        self.assertTrue(len(app.selectbox[0].options)>0)
        app.button[0].click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any('Pembanding snapshot' in item.value for item in app.markdown))

if __name__ == '__main__':
    unittest.main()
