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
        workspace = next(w for w in result['workspaces'] if w['id'] == 'example')
        charts = [r for r in workspace['resources'] if r.get('chartType') in {'html', 'vega_lite'}]
        self.assertEqual(len(charts), 14)
        self.assertEqual(workspace['requiredConnections'], [{'alias': 'github_example', 'type': 'key-value'}, {'alias': 'http_example', 'type': 'key-value'}])
        for chart in charts:
            self.assertIn('data/example/renderer-sales.csv', chart['files'])
            self.assertEqual(chart['requiredConnections'], [])
            self.assertEqual(chart['preview']['path'], f"previews/{chart['resourceID']}.png")
        self.assertEqual({r['chartType'] for r in charts}, {'html', 'vega_lite'})
        dashboard = next(r for r in workspace['resources'] if r['resourceID'] == 'renderer_gallery')
        self.assertEqual(set(dashboard['files']), {r['path'] for r in charts} | {
            dashboard['path'], 'data/example/renderer-sales.csv'})
        self.assertEqual(dashboard['requiredConnections'], [])

    def test_new_renderers_reject_script_and_native_field_mixtures(self):
        path = ROOT / 'workspaces/example/charts/Example/Gallery/HTML/html_cards.yaml'
        original = yaml.safe_load(path.read_text())
        for change in ['js', 'scripts', 'plot', 'missing_html']:
            document = copy.deepcopy(original)
            if change == 'js': document['chart']['option']['js'] = 'alert(1)'
            elif change == 'missing_html': del document['chart']['option']['html']
            else: document['chart'][change] = 'invalid'
            with self.subTest(change=change):
                with self.assertRaises(ValueError):
                    validation.validate_chart(document, 'test')
