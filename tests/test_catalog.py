import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import yaml

spec = importlib.util.spec_from_file_location("build_catalog", Path(__file__).parents[1] / "scripts/build_catalog.py")
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.topic = self.root / "example"
        (self.topic / "charts").mkdir(parents=True)
        (self.topic / "dashboards").mkdir()
        (self.topic / "data").mkdir()
        (self.topic / "workspace.json").write_text(json.dumps({"id": "example", "title": "Example", "kind": "localPath"}))
        (self.topic / "data/prices.csv").write_text("x,y\n1,2\n")
        self.chart = {"sources": {"prices": {"source": "duckdb", "file": "data/prices.csv"}},
                      "dataset": {"id": "prices", "sources": [{"id": "raw", "ref": "#/sources/prices"}]},
                      "chart": {"id": "price", "title": "Prices", "plot": "line"}}
        self.write_chart("price", self.chart)

    def write_chart(self, name, chart):
        (self.topic / f"charts/{name}.yaml").write_text(yaml.safe_dump(chart))

    def build(self):
        return catalog.build_catalog(self.root, "a" * 40)

    def test_dependency_closure_and_deterministic_metadata(self):
        derived = copy.deepcopy(self.chart)
        derived["chart"]["id"] = "derived"
        derived["sources"] = {}
        derived["dataset"] = {"id": "derived", "ref": "price.yaml#/dataset"}
        self.write_chart("derived", derived)
        dashboard = {"kind": "Dashboard", "id": "overview", "title": "Overview",
                     "tabs": [{"id": "main", "panels": [{"id": "price", "chart": "derived"}]}]}
        (self.topic / "dashboards/overview.yaml").write_text(yaml.safe_dump(dashboard))
        result = self.build()
        self.assertEqual(result, self.build())
        item = next(item for item in result["workspaces"][0]["resources"] if item["type"] == "dashboard")
        self.assertEqual(item["files"], ["charts/derived.yaml", "charts/price.yaml", "dashboards/overview.yaml", "data/prices.csv"])
        self.assertEqual(item["sourceKinds"], ["duckdb"])
        self.assertNotIn("tags", result["workspaces"][0])
        self.assertTrue(all("tags" not in resource for resource in result["workspaces"][0]["resources"]))

    def test_cross_workspace_refs_and_missing_files_are_rejected(self):
        for ref in ["../other/charts/price.yaml#/dataset", "other/price.yaml#/dataset", "missing.yaml#/dataset"]:
            with self.subTest(ref=ref):
                self.chart["dataset"] = {"id": "prices", "ref": ref}
                self.write_chart("price", self.chart)
                with self.assertRaises(ValueError):
                    self.build()

    def test_cross_workspace_dashboard_is_rejected(self):
        dashboard = {"kind": "Dashboard", "id": "overview", "title": "Overview",
                     "tabs": [{"panels": [{"chart": "other/price"}]}]}
        (self.topic / "dashboards/overview.yaml").write_text(yaml.safe_dump(dashboard))
        with self.assertRaises(ValueError):
            self.build()

    def test_cycles_are_rejected(self):
        other = copy.deepcopy(self.chart)
        other["chart"]["id"] = "other"
        other["dataset"] = {"id": "other", "ref": "price.yaml#/dataset"}
        self.chart["dataset"] = {"id": "prices", "ref": "other.yaml#/dataset"}
        self.write_chart("other", other)
        self.write_chart("price", self.chart)
        with self.assertRaises(ValueError):
            self.build()

    def test_data_path_traversal_and_symlinks_are_rejected(self):
        for path in ["../other/data/prices.csv", "/data/prices.csv", "data/../prices.csv"]:
            self.chart["sources"]["prices"]["file"] = path
            self.write_chart("price", self.chart)
            with self.assertRaises(ValueError):
                self.build()
        self.chart["sources"]["prices"]["file"] = "data/prices.csv"
        self.write_chart("price", self.chart)
        (self.topic / "data/prices.csv").unlink()
        (self.root / "outside.csv").write_text("private")
        (self.topic / "data/prices.csv").symlink_to(self.root / "outside.csv")
        with self.assertRaises(ValueError):
            self.build()

    def test_missing_data_and_duplicate_ids_are_rejected(self):
        (self.topic / "data/prices.csv").unlink()
        with self.assertRaises(ValueError):
            self.build()
        (self.topic / "data/prices.csv").write_text("x,y\n1,2")
        (self.topic / "charts/nested").mkdir()
        (self.topic / "charts/nested/price.yaml").write_text(yaml.safe_dump(self.chart))
        with self.assertRaises(ValueError):
            self.build()


if __name__ == "__main__":
    unittest.main()
