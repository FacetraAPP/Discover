import copy
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml

from scripts import build_catalog as catalog
from scripts import validate_yaml as validation

ROOT = Path(__file__).resolve().parents[1]


class YAMLValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.topic = self.root / "sales"
        shutil.copytree(ROOT / "docs/starter", self.topic)
        self.chart_path = self.topic / "charts/sales.yaml"
        self.dashboard_path = self.topic / "dashboards/overview.yaml"
        self.chart = validation.load_yaml(self.chart_path.read_bytes(), str(self.chart_path))
        self.dashboard = validation.load_yaml(self.dashboard_path.read_bytes(), str(self.dashboard_path))

    def write(self, path, document):
        path.write_text(yaml.safe_dump(document), encoding="utf-8")

    def build(self):
        return catalog.build_catalog(self.root, "a" * 40)

    def test_starter_is_a_complete_installable_workspace(self):
        workspace = self.build()["workspaces"][0]
        self.assertEqual(workspace["requiredConnections"], [])
        dashboard = next(item for item in workspace["resources"] if item["type"] == "dashboard")
        self.assertEqual(dashboard["files"], ["charts/sales.yaml", "dashboards/overview.yaml", "data/sales.csv"])

    def test_documented_complete_dashboards_are_valid(self):
        guide = (ROOT / "docs/dashboard-yaml.md").read_text()
        documents = re.findall(r"~~~yaml\n(.*?)\n~~~", guide, re.DOTALL)
        self.assertEqual(len(documents), 2)
        for snippet in documents:
            document = validation.load_yaml(snippet, "dashboard guide")
            validation.validate_dashboard(document, {"sales": self.chart}, "dashboard guide")

    def test_duplicate_keys_and_nonstring_mapping_keys_are_rejected(self):
        for snippet in ["id: sales\nid: other\n", "true: value\n", "id: &id sales\n<<: {id: other}\n"]:
            with self.subTest(snippet=snippet):
                self.chart_path.write_text(snippet)
                with self.assertRaisesRegex(ValueError, "sales/charts/sales.yaml"):
                    self.build()

    def test_scientific_notation_is_numeric_but_quoted_numbers_are_not(self):
        self.chart_path.write_text(self.chart_path.read_text().replace("minimum: 0", "minimum: 1e+0").replace("default: 0", "default: 2e+0"))
        self.dashboard["params"][0]["default"] = 2
        self.write(self.dashboard_path, self.dashboard)
        self.build()
        self.dashboard["tabs"][0]["panels"][0]["height"] = "240"
        self.write(self.dashboard_path, self.dashboard)
        with self.assertRaisesRegex(ValueError, "finite number"):
            self.build()

    def test_workspace_fields_types_and_connections_are_checked(self):
        original = yaml.safe_load((self.topic / "workspace.yaml").read_text())
        for field, value in [("kind", "remoteSync"), ("title", []), ("isPersonal", "false"),
                             ("requiredConnections", "business"), ("requiredConnections", ["business", "business"]),
                             ("localDirectory", "/private/workspace")]:
            with self.subTest(field=field, value=value):
                manifest = dict(original, **{field: value})
                self.write(self.topic / "workspace.yaml", manifest)
                with self.assertRaisesRegex(ValueError, "sales/workspace.yaml"):
                    self.build()

    def test_invalid_chart_shapes_and_renderer_mixtures_are_rejected(self):
        for field, value in [("dataset", "missing"), ("renderer", "unknown"), ("x", ""),
                             ("x", 1), ("option", None), ("plot", "scatter"), ("notes", []),
                             ("unknown", "typo")]:
            with self.subTest(field=field, value=value):
                document = copy.deepcopy(self.chart)
                document["chart"][field] = value
                self.write(self.chart_path, document)
                with self.assertRaisesRegex(ValueError, "sales/charts/sales.yaml"):
                    self.build()

    def test_parameter_types_defaults_and_ranges_are_checked(self):
        for update in [{"type": "date"}, {"type": "integer", "default": True},
                       {"default": "0"}, {"default": -1}, {"minimum": 10, "maximum": 1},
                       {"options": [1, 2]}, {"required": "true"}, {"maximum": float("inf")}]:
            with self.subTest(update=update):
                document = copy.deepcopy(self.chart)
                document["params"][0].update(update)
                self.write(self.chart_path, document)
                with self.assertRaisesRegex(ValueError, "params"):
                    self.build()

    def test_date_parameters_use_iso_and_validate_calendar_dates(self):
        from scripts.validate_yaml import parameters
        valid = {"name": "day", "type": "date", "default": "2024-02-29"}
        self.assertEqual(parameters([valid], "dates")["day"]["default"], "2024-02-29")
        for value in ["20240229", "2026-02-29", "2026-2-01", "2026-13-01", "0000-01-01", "+2026-01-01"]:
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "ISO calendar date"):
                parameters([dict(valid, default=value)], "dates")
        with self.assertRaisesRegex(ValueError, "numeric bounds"):
            parameters([dict(valid, minimum=1)], "dates")

    def test_source_variants_and_http_fields_are_checked(self):
        invalid = [{"source": "healthkit"}, {"source": "duckdb"},
                   {"source": "duckdb", "file": "data/sales.csv", "sql": "SELECT 1"},
                   {"source": "database", "connection": "business"},
                   {"source": "sqlite", "file_path": "orders.sqlite"},
                   {"ref": "#/sources/sales", "file": "data/sales.csv"},
                   {"source": "http", "url": "http://example.org"},
                   {"source": "http", "url": "https://example.org", "json": {}},
                   {"source": "http", "url": "https://example.org", "method": "post", "json": {}, "data": {}},
                   {"source": "http", "url": "https://example.org", "params": {"nested": []}},
                   {"source": "http", "url": "https://example.org", "recordsPath": ["data"], "format": "csv"}]
        for definition in invalid:
            with self.subTest(definition=definition):
                document = copy.deepcopy(self.chart)
                document["sources"]["sales"] = definition
                self.write(self.chart_path, document)
                with self.assertRaisesRegex(ValueError, "sources.sales"):
                    self.build()

    def test_valid_http_database_and_sqlite_are_offline(self):
        definitions = [
            {"source": "http", "url": "{{ connections.market.endpoint }}", "format": "json"},
            {"source": "database", "connection": "business", "sql": "SELECT 1 AS revenue"},
            {"source": "sqlite", "file_path": "orders.sqlite", "sql": "SELECT 1 AS revenue"}]
        (self.topic / "data/orders.sqlite").write_bytes(b"offline fixture; validator does not query it")
        for definition in definitions:
            with self.subTest(definition=definition):
                document = copy.deepcopy(self.chart)
                document["sources"]["sales"] = definition
                self.write(self.chart_path, document)
                workspace = self.build()["workspaces"][0]
                resource = next(item for item in workspace["resources"] if item["type"] == "chart")
                self.assertEqual(resource["sourceKinds"], [definition["source"]])
                self.assertEqual(resource["requiredConnections"], {"http": ["market"], "database": ["business"], "sqlite": []}[definition["source"]])

    def test_request_json_keys_do_not_become_catalog_dependencies(self):
        self.chart["sources"]["sales"] = {"source": "http", "url": "https://example.org",
            "method": "post", "json": {"file": "not-a-file", "ref": "not-a-reference", "connection": "not-a-connection"}}
        self.write(self.chart_path, self.chart)
        workspace = self.build()["workspaces"][0]
        resource = next(item for item in workspace["resources"] if item["type"] == "chart")
        self.assertEqual(resource["files"], ["charts/sales.yaml"])
        self.assertEqual(resource["requiredConnections"], [])

    def test_json_recursive_aliases_are_rejected_with_context(self):
        self.chart["sources"]["sales"] = {"source": "http", "url": "https://example.org", "method": "post"}
        body = {}
        body["recursive"] = body
        self.chart["sources"]["sales"]["json"] = body
        self.write(self.chart_path, self.chart)
        with self.assertRaisesRegex(ValueError, "recursive alias"):
            self.build()

    def test_dataset_inputs_and_reference_kinds_are_checked(self):
        for dataset in [{"id": "monthly_sales", "sources": []},
                        {"id": "monthly_sales", "sources": [{"id": "raw", "ref": "#/dataset"}]},
                        {"id": "monthly_sales", "sources": [{"id": "raw", "ref": "#/sources/sales"}, {"id": "RAW", "ref": "#/sources/sales"}]},
                        {"id": "monthly_sales", "ref": "sales.yaml#/dataset", "sql": "SELECT 1"},
                        {"id": "monthly_sales", "sources": [{"id": "one", "ref": "#/sources/sales"}, {"id": "two", "ref": "#/sources/sales"}]}]:
            with self.subTest(dataset=dataset):
                document = copy.deepcopy(self.chart)
                document["dataset"] = dataset
                self.write(self.chart_path, document)
                with self.assertRaisesRegex(ValueError, "sales/charts/sales.yaml"):
                    self.build()

    def test_same_file_source_and_dataset_cycles_are_rejected(self):
        for change in ["source", "dataset"]:
            with self.subTest(change=change):
                document = copy.deepcopy(self.chart)
                if change == "source":
                    document["sources"]["sales"] = {"ref": "#/sources/sales"}
                else:
                    document["dataset"] = {"id": "monthly_sales", "ref": "#/dataset"}
                self.write(self.chart_path, document)
                with self.assertRaisesRegex(ValueError, "cyclic"):
                    self.build()

    def test_external_reference_bindings_and_dependency_closure(self):
        derived = copy.deepcopy(self.chart)
        derived["chart"]["id"] = "derived"
        derived["sources"] = {}
        derived["dataset"] = {"id": "monthly_sales", "ref": "sales.yaml#/dataset", "with": {"min_revenue": {"param": "min_revenue"}}}
        path = self.topic / "charts/derived.yaml"
        self.write(path, derived)
        resource = next(item for item in self.build()["workspaces"][0]["resources"] if item["resourceID"] == "derived")
        self.assertEqual(resource["files"], ["charts/derived.yaml", "charts/sales.yaml", "data/sales.csv"])
        for arguments in [{"unknown": 0}, {"min_revenue": "zero"},
                          {"min_revenue": {"param": "missing"}}, {"min_revenue": -1}]:
            with self.subTest(arguments=arguments):
                derived["dataset"]["with"] = arguments
                self.write(path, derived)
                with self.assertRaisesRegex(ValueError, "charts/derived.yaml.dataset.with"):
                    self.build()

    def test_value_renderer_and_echarts_bindings(self):
        self.chart["chart"] = {"id": "sales", "title": "Sales", "dataset": "monthly_sales", "renderer": "value", "value": "revenue"}
        self.write(self.chart_path, self.chart)
        self.build()
        self.chart["chart"] = {"id": "sales", "title": "Sales", "dataset": "monthly_sales", "renderer": "echarts",
                               "scripts": {"format": "(v) => v"}, "option": {}}
        valid = [{"from": "monthly_sales", "field": "revenue"},
                 {"from": "monthly_sales", "fields": ["month", "revenue"], "color_by": ["revenue", "revenue"]},
                 {"from": "monthly_sales", "x": "month", "y": "revenue"},
                 {"from": "monthly_sales", "rows": True},
                 {"from": "params", "name": "min_revenue"}, {"from": "script", "name": "format"}]
        invalid = [{"from": "wrong", "field": "revenue"}, {"from": "monthly_sales", "field": "revenue", "rows": True},
                   {"from": "monthly_sales", "x": "month"}, {"from": "monthly_sales", "fields": []},
                   {"from": "params", "name": "missing"}, {"from": "script", "name": "missing"},
                   {"from": "monthly_sales", "rows": False}, {"from": "monthly_sales", "rows": True, "color_by_sign": True}]
        for binding in valid + invalid:
            with self.subTest(binding=binding):
                self.chart["chart"]["option"] = {"series": [{"data": binding}]}
                self.write(self.chart_path, self.chart)
                if binding in valid:
                    self.build()
                else:
                    with self.assertRaisesRegex(ValueError, "chart.option"):
                        self.build()

    def test_dashboard_structure_ids_and_layout_are_checked(self):
        original = copy.deepcopy(self.dashboard)
        cases = [{"version": True}, {"version": 2}, {"tabs": []}, {"params": {}},
                 {"tabs": [{"id": "a", "title": "A", "panels": [], "unexpected": 1}]}]
        for update in cases:
            with self.subTest(update=update):
                self.write(self.dashboard_path, dict(original, **update))
                with self.assertRaisesRegex(ValueError, "sales/dashboards/overview.yaml"):
                    self.build()
        panel = original["tabs"][0]["panels"][0]
        for update in [{"chart": "missing"}, {"height": 159}, {"width": 1},
                       {"row_span": 4}, {"responsive": {"compact": {"card_height": 300}}}]:
            with self.subTest(update=update):
                document = copy.deepcopy(original)
                document["tabs"][0]["panels"][0] = dict(panel, **update)
                self.write(self.dashboard_path, document)
                with self.assertRaisesRegex(ValueError, "sales/dashboards/overview.yaml"):
                    self.build()
        document = copy.deepcopy(original)
        other_tab = copy.deepcopy(document["tabs"][0])
        other_tab["id"] = "another"
        document["tabs"].append(other_tab)
        self.write(self.dashboard_path, document)
        with self.assertRaisesRegex(ValueError, "panels: IDs must be unique"):
            self.build()

    def test_dashboard_parameter_bindings_are_checked(self):
        for value in [{"unknown": 1}, {"min_revenue": {"param": "missing"}},
                      {"min_revenue": "zero"}, {"min_revenue": -1},
                      {"min_revenue": {"param": "threshold", "extra": 1}}]:
            with self.subTest(value=value):
                document = copy.deepcopy(self.dashboard)
                document["tabs"][0]["panels"][0]["params"] = value
                self.write(self.dashboard_path, document)
                with self.assertRaisesRegex(ValueError, "panels.params"):
                    self.build()
        self.chart["params"][0].pop("default")
        self.write(self.chart_path, self.chart)
        self.dashboard["tabs"][0]["panels"][0]["params"] = {}
        self.write(self.dashboard_path, self.dashboard)
        with self.assertRaisesRegex(ValueError, "missing required target parameter"):
            self.build()

    def test_dashboard_requires_notes_even_when_empty(self):
        self.dashboard.pop("notes")
        self.write(self.dashboard_path, self.dashboard)
        with self.assertRaisesRegex(ValueError, "missing fields.*notes"):
            self.build()
        self.dashboard["notes"] = ""
        self.write(self.dashboard_path, self.dashboard)
        self.build()

    def test_grid_defaults_and_invalid_dimensions(self):
        original = copy.deepcopy(self.dashboard)
        original["tabs"][0]["layout"] = {"type": "grid"}
        self.write(self.dashboard_path, original)
        self.build()
        for update in [{"columns": 13}, {"columns": True}, {"row_height": 23},
                       {"gap": -1}, {"min_width": 319}]:
            with self.subTest(update=update):
                document = copy.deepcopy(original)
                document["tabs"][0]["layout"].update(update)
                self.write(self.dashboard_path, document)
                with self.assertRaisesRegex(ValueError, "layout"):
                    self.build()
        for update in [{"width": 13}, {"row_span": 1},
                       {"responsive": {"compact": {"card_height": 601}}}]:
            with self.subTest(update=update):
                document = copy.deepcopy(original)
                document["tabs"][0]["panels"][0].update(update)
                self.write(self.dashboard_path, document)
                with self.assertRaisesRegex(ValueError, "sales/dashboards/overview.yaml"):
                    self.build()

    def test_manifestless_topics_and_yml_files_do_not_pass_silently(self):
        (self.topic / "workspace.yaml").unlink()
        with self.assertRaisesRegex(ValueError, "exactly one workspace"):
            self.build()
        shutil.copyfile(ROOT / "docs/starter/workspace.yaml", self.topic / "workspace.yml")
        with self.assertRaisesRegex(ValueError, "use workspace.yaml"):
            self.build()
        (self.topic / "workspace.yml").rename(self.topic / "workspace.yaml")
        (self.topic / "charts/nested").mkdir()
        self.chart_path.rename(self.topic / "charts/nested/sales.yml")
        with self.assertRaisesRegex(ValueError, "use the .yaml extension"):
            self.build()

    def test_validate_only_cli_reports_failures_and_does_not_write_files(self):
        command = [sys.executable, str(ROOT / "scripts/build_catalog.py"),
                   "--root", str(self.root), "--revision", "a" * 40, "--validate-only"]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Validated 1 workspaces and 2", result.stdout)
        self.assertFalse((self.root / "discover.json").exists())
        self.chart["chart"]["dataset"] = "wrong"
        self.write(self.chart_path, self.chart)
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("sales/charts/sales.yaml", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_catalog_export_remains_deterministic(self):
        shutil.copyfile(ROOT / "LICENSE", self.root / "LICENSE")
        output = self.root / "dist"
        command = [sys.executable, str(ROOT / "scripts/build_catalog.py"), "--root", str(self.root),
                   "--revision", "a" * 40, "--output", str(output)]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads((output / "discover.json").read_text()), self.build())
        self.assertEqual((output / "LICENSE").read_bytes(), (ROOT / "LICENSE").read_bytes())


    def test_tags_are_published_and_normalized_for_both_resource_types(self):
        self.chart["chart"]["tags"] = [" 股票 ", "Macro", "macro", "Café", "cafe"]
        self.dashboard["tags"] = ["股票", "分析"]
        self.write(self.chart_path, self.chart)
        self.write(self.dashboard_path, self.dashboard)
        resources = self.build()["workspaces"][0]["resources"]
        self.assertEqual(next(r for r in resources if r["type"] == "chart")["tags"], ["股票", "Macro", "Café"])
        self.assertEqual(next(r for r in resources if r["type"] == "dashboard")["tags"], ["股票", "分析"])

    def test_malformed_tags_are_rejected_with_file_context(self):
        for value in ["macro", None, [True], [42], [""], [" "], ["a" * 65], ["a\nb"]]:
            with self.subTest(value=value):
                self.chart["chart"]["tags"] = value
                self.write(self.chart_path, self.chart)
                with self.assertRaisesRegex(ValueError, "sales/charts/sales.yaml.*tags"):
                    self.build()


if __name__ == "__main__":
    unittest.main()
