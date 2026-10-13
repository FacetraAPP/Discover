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

    def test_yaml_manifest_and_readme_are_published_with_digests(self):
        manifest = {"id": "example", "title": "YAML workspace", "kind": "localPath"}
        (self.topic / "workspace.json").unlink()
        (self.topic / "workspace.yaml").write_text(yaml.safe_dump(manifest))
        markdown = "# Guide\n\n## Setup\n\n- Configure **market**\n"
        (self.topic / "README.md").write_text(markdown, encoding="utf-8")
        workspace = self.build()["workspaces"][0]
        files = {file["path"]: file for file in workspace["files"]}
        self.assertEqual(workspace["title"], "YAML workspace")
        self.assertIn("workspace.yaml", files)
        self.assertNotIn("workspace.json", files)
        self.assertEqual(files["README.md"], catalog.file_record(self.topic, "README.md"))
        self.assertNotIn("README.md", workspace["resources"][0]["files"])
        self.assertNotIn(markdown, json.dumps(workspace))

    def test_legacy_json_and_lowercase_readme_remain_supported(self):
        (self.topic / "readme.md").write_text("# Legacy Guide\n")
        files = {file["path"] for file in self.build()["workspaces"][0]["files"]}
        self.assertTrue({"workspace.json", "readme.md"}.issubset(files))

    def test_multiple_manifests_invalid_yaml_and_readme_links_are_rejected(self):
        manifest = self.topic / "workspace.yaml"
        manifest.write_text("id: example\ntitle: YAML\nkind: localPath\n")
        with self.assertRaises(ValueError):
            self.build()
        (self.topic / "workspace.json").unlink()
        for text in ["[]", "null", "id: [broken"]:
            with self.subTest(text=text):
                manifest.write_text(text)
                with self.assertRaises((ValueError, yaml.YAMLError)):
                    self.build()
        manifest.write_text("id: example\ntitle: YAML\nkind: localPath\n")
        (self.root / "outside.md").write_text("private")
        (self.topic / "README.md").symlink_to(self.root / "outside.md")
        with self.assertRaises(ValueError):
            self.build()
        (self.topic / "README.md").unlink()
        (self.topic / "README.md").write_bytes(b"\xff")
        with self.assertRaises(ValueError):
            self.build()

    def test_workspace_metadata_comes_from_manifest_without_resource_inheritance(self):
        manifest = {"id": "example", "title": "Workspace title", "kind": "localPath",
                    "description": "Workspace description", "license": "MIT"}
        (self.topic / "workspace.json").write_text(json.dumps(manifest))
        self.chart["chart"]["notes"] = "Chart description"
        self.write_chart("price", self.chart)
        workspace = self.build()["workspaces"][0]
        self.assertEqual(workspace["title"], manifest["title"])
        self.assertEqual(workspace["description"], manifest["description"])
        self.assertEqual(workspace["license"], manifest["license"])
        self.assertEqual(workspace["resources"][0]["title"], "Prices")
        self.assertEqual(workspace["resources"][0]["description"], "Chart description")

    def test_optional_workspace_metadata_defaults_and_invalid_types(self):
        workspace = self.build()["workspaces"][0]
        self.assertEqual(workspace["description"], "")
        self.assertEqual(workspace["license"], "Apache-2.0")
        for field, value in [("description", []), ("license", {})]:
            with self.subTest(field=field):
                manifest = {"id": "example", "title": "Example", "kind": "localPath", field: value}
                (self.topic / "workspace.json").write_text(json.dumps(manifest))
                with self.assertRaises(ValueError):
                    self.build()

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


class PublishedExampleTests(unittest.TestCase):
    def test_published_example_has_no_health_sources_or_dangling_references(self):
        root = Path(__file__).resolve().parents[1]
        result = catalog.build_catalog(root, "0" * 40)
        example = next(w for w in result["workspaces"] if w["id"] == "example")
        self.assertEqual(sum(r["type"] == "chart" for r in example["resources"]), 8)
        self.assertEqual(sum(r["type"] == "dashboard" for r in example["resources"]), 3)
        self.assertFalse(any("health" in f["path"] for f in example["files"]))
        self.assertTrue({"workspace.yaml", "README.md"}.issubset({f["path"] for f in example["files"]}))
        self.assertFalse(any("healthkit" in r["sourceKinds"] for r in example["resources"]))
