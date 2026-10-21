import copy
from pathlib import Path
import unittest
import yaml
from scripts import build_catalog as catalog
from scripts import validate_yaml as validation

ROOT = Path(__file__).resolve().parents[1]

class DeclarativeRendererTests(unittest.TestCase):
    def test_gallery_is_installable_with_local_dependencies(self):
        result = catalog.build_catalog(ROOT, 'a' * 40)
        workspace = next(w for w in result['workspaces'] if w['id'] == 'renderers')
        charts = [r for r in workspace['resources'] if r['type'] == 'chart']
        self.assertEqual(len(charts), 14)
        self.assertEqual(workspace['requiredConnections'], [])
        for chart in charts:
            self.assertIn('data/sales.csv', chart['files'])
        self.assertEqual({r['chartType'] for r in charts}, {'html', 'vega_lite'})

    def test_new_renderers_reject_script_and_native_field_mixtures(self):
        path = ROOT / 'workspaces/renderers/charts/HTML/html_cards.yaml'
        original = yaml.safe_load(path.read_text())
        for change in ['js', 'scripts', 'plot', 'missing_html']:
            document = copy.deepcopy(original)
            if change == 'js': document['chart']['option']['js'] = 'alert(1)'
            elif change == 'missing_html': del document['chart']['option']['html']
            else: document['chart'][change] = 'invalid'
            with self.subTest(change=change):
                with self.assertRaises(ValueError):
                    validation.validate_chart(document, 'test')
