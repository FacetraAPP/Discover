import copy
import json
from pathlib import Path
import tempfile
import unittest

import yaml

from scripts import build_catalog as catalog


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.topic = self.root / "workspaces/example"
        (self.topic / "charts").mkdir(parents=True)
        (self.topic / "dashboards").mkdir()
        (self.topic / "data").mkdir()
        (self.topic / "workspace.json").write_text(json.dumps({"id": "example", "title": "Example", "kind": "localPath"}))
        (self.topic / "data/prices.csv").write_text("x,y\n1,2\n")
        self.chart = {"sources": {"prices": {"source": "duckdb", "file": "data/prices.csv"}},
                      "dataset": {"id": "prices", "sources": [{"id": "raw", "ref": "#/sources/prices"}]},
                      "metadata": {"id": "price", "title": "Prices"}, "chart": {"dataset": "prices", "renderer": "default", "plot": "line", "x": "x", "y": "y"}}
        self.write_chart("price", self.chart)

    def write_chart(self, name, chart):
        (self.topic / f"charts/{name}.yaml").write_text(yaml.safe_dump(chart))

    def build(self):
        return catalog.build_catalog(self.root, "a" * 40)

    def test_resource_summaries_use_fallback_and_workspace_text_stays_fixed(self):
        self.chart["metadata"].update(title={"i18n": "title"}, notes={"i18n": "notes"})
        self.chart["i18n"] = {"defaultLocale": "zh-Hans", "messages": {
            "title": {"zh-Hans": "价格", "en": "Prices"},
            "notes": {"zh-Hans": "默认说明", "EN-gb": "British notes"}}}
        self.write_chart("price", self.chart)
        manifest = {"title": "Default workspace", "description": "Fixed notes"}
        (self.topic / "workspace.json").unlink()
        (self.topic / "workspace.yaml").write_text(yaml.safe_dump(manifest))
        workspace = self.build()["workspaces"][0]
        resource = workspace["resources"][0]
        self.assertEqual(workspace["title"], "Default workspace")
        self.assertEqual(workspace["description"], "Fixed notes")
        self.assertNotIn("localizations", workspace)
        self.assertNotIn("i18n", workspace)
        self.assertEqual(resource["title"], "价格")
        self.assertEqual(resource["localizations"]["en"], {"title": "Prices", "description": "默认说明"})
        self.assertEqual(resource["localizations"]["EN-gb"], {"title": "Prices", "description": "British notes"})
        self.assertEqual(resource["localizations"]["zh-Hans"], {"title": "价格", "description": "默认说明"})

    def test_workspace_rejects_translation_configuration_without_compatibility(self):
        for filename in ("workspace.yaml", "workspace.json"):
            for field in ("localizations", "i18n"):
                for value in ({}, None, {"en": {"title": "English"}}):
                    with self.subTest(filename=filename, field=field, value=value):
                        for previous in self.topic.glob("workspace.*"):
                            previous.unlink()
                        (self.topic / filename).write_text(json.dumps({"title": "Example", field: value}))
                        with self.assertRaisesRegex(ValueError, "unsupported fields.*" + field):
                            self.build()

    def test_workspace_rejects_translation_references_on_title_and_description(self):
        for field in ("title", "description"):
            with self.subTest(field=field):
                manifest = {"title": "Fixed title", field: {"i18n": field}}
                (self.topic / "workspace.json").write_text(json.dumps(manifest))
                with self.assertRaisesRegex(ValueError, "expected a .*string"):
                    self.build()

    def test_all_published_summaries_have_chinese_and_english(self):
        result = catalog.build_catalog(Path(__file__).resolve().parents[1], "a" * 40)
        for workspace in result["workspaces"]:
            self.assertNotIn("localizations", workspace)
            self.assertTrue(workspace["title"].strip())
            for item in workspace["resources"]:
                with self.subTest(item=item["id"]):
                    self.assertIn("zh-Hans", item["localizations"])
                    english = item["localizations"]["en"]
                    self.assertTrue(english["title"].strip())
                    if item["description"].strip():
                        self.assertTrue(english["description"].strip())
                    self.assertNotRegex(english["title"] + english["description"], r"[\u3400-\u9fff]")

    def test_only_workspaces_content_is_discovered_and_ids_remain_stable(self):
        for name in ["docs/starter", "scripts", "tests", "legacy-topic"]:
            folder = self.root / name
            folder.mkdir(parents=True)
            (folder / "workspace.yaml").write_text("invalid: repository tooling is not content\n")
        workspace = self.build()["workspaces"][0]
        self.assertEqual(workspace["id"], "example")
        self.assertEqual(workspace["path"], "workspaces/example")
        self.assertTrue(all(resource["id"].startswith("example/") for resource in workspace["resources"]))
        self.assertTrue(all(not file["path"].startswith("workspaces/") for file in workspace["files"]))

    def test_content_root_and_workspace_symlinks_are_rejected(self):
        content_root = self.root / "workspaces"
        (content_root / "linked").symlink_to(self.topic, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "Workspace directories cannot be symbolic links"):
            self.build()
        (content_root / "linked").unlink()
        content_root.rename(self.root / "outside")
        content_root.symlink_to(self.root / "outside", target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "workspaces/ cannot be a symbolic link"):
            self.build()

    def test_yaml_manifest_and_readme_are_published_with_digests(self):
        manifest = {"title": "YAML workspace"}
        (self.topic / "workspace.json").unlink()
        (self.topic / "workspace.yaml").write_text(yaml.safe_dump(manifest))
        markdown = "# Guide\n\n## Setup\n\n- Configure **market**\n"
        (self.topic / "README.md").write_text(markdown, encoding="utf-8")
        workspace = self.build()["workspaces"][0]
        files = {file["path"]: file for file in workspace["files"]}
        self.assertEqual(workspace["title"], "YAML workspace")
        self.assertEqual(workspace["id"], "example")
        self.assertEqual(workspace["path"], "workspaces/example")
        self.assertTrue(all(item["id"].startswith("example/") for item in workspace["resources"]))
        self.assertIn("workspace.yaml", files)
        self.assertNotIn("workspace.json", files)
        self.assertEqual(files["README.md"], catalog.file_record(self.topic, "README.md"))
        self.assertNotIn("README.md", workspace["resources"][0]["files"])
        self.assertNotIn(markdown, json.dumps(workspace))

    def test_legacy_json_and_lowercase_readme_remain_supported(self):
        (self.topic / "readme.md").write_text("# Legacy Guide\n")
        files = {file["path"] for file in self.build()["workspaces"][0]["files"]}
        self.assertTrue({"workspace.json", "readme.md"}.issubset(files))

    def test_connection_type_is_included_in_complete_workspace_without_credentials(self):
        folder = self.topic / "connections"
        folder.mkdir()
        definition = folder / "ftshare.yaml"
        definition.write_text("name: FTShare\nfields: [{key: endpoint}, {key: api_key}]\n")
        workspace = self.build()["workspaces"][0]
        files = {file["path"]: file for file in workspace["files"]}
        self.assertEqual(files["connections/ftshare.yaml"], catalog.file_record(self.topic, "connections/ftshare.yaml"))
        self.assertEqual(workspace["requiredConnections"], [])
        self.assertNotIn("connections/ftshare.yaml", workspace["resources"][0]["files"])

    def test_invalid_connection_types_are_rejected(self):
        folder = self.topic / "connections"
        folder.mkdir()
        definition = folder / "ftshare.yaml"
        for text in ["fields: [{key: api_key, value: secret}]", "fields: [{key: bad.key}]",
                     "fields: [{key: api_key}, {key: api_key}]", "fields: token",
                     "name: ''\nfields: []", "fields: [{key: token}]\napi_key: secret"]:
            with self.subTest(text=text):
                definition.write_text(text)
                with self.assertRaisesRegex(ValueError, "example/connections/ftshare.yaml"):
                    self.build()
        definition.unlink()
        (folder / "nested").mkdir()
        (folder / "nested/ftshare.yaml").write_text("fields: []")
        with self.assertRaisesRegex(ValueError, "connections/<type-id>.yaml"):
            self.build()

    def test_connection_type_symlinks_and_yml_are_rejected(self):
        folder = self.topic / "connections"
        folder.mkdir()
        (self.root / "outside.yaml").write_text("fields: []")
        definition = folder / "ftshare.yaml"
        definition.symlink_to(self.root / "outside.yaml")
        with self.assertRaisesRegex(ValueError, "Symbolic links"):
            self.build()
        definition.unlink()
        (folder / "ftshare.yml").write_text("fields: []")
        with self.assertRaisesRegex(ValueError, "use the .yaml extension"):
            self.build()
        (folder / "ftshare.yml").unlink()
        folder.rmdir()
        folder.symlink_to(self.root)
        with self.assertRaisesRegex(ValueError, "connections/ cannot be a symbolic link"):
            self.build()

    def test_multiple_manifests_invalid_yaml_and_readme_links_are_rejected(self):
        manifest = self.topic / "workspace.yaml"
        manifest.write_text("title: YAML\n")
        with self.assertRaises(ValueError):
            self.build()
        (self.topic / "workspace.json").unlink()
        for text in ["[]", "null", "id: [broken"]:
            with self.subTest(text=text):
                manifest.write_text(text)
                with self.assertRaises((ValueError, yaml.YAMLError)):
                    self.build()
        manifest.write_text("title: YAML\n")
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
        self.chart["metadata"]["notes"] = "Chart description"
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
        derived["metadata"]["id"] = "derived"
        derived["sources"] = {}
        derived["dataset"] = {"id": "derived", "ref": "price.yaml#/dataset"}
        derived["chart"]["dataset"] = "derived"
        self.write_chart("derived", derived)
        dashboard = {"version": 1, "kind": "Dashboard", "metadata": {"id": "overview", "title": "Overview", "notes": ""}, "params": [],
                     "tabs": [{"id": "main", "title": "Main", "panels": [{"id": "price", "chart": "derived"}]}]}
        (self.topic / "dashboards/overview.yaml").write_text(yaml.safe_dump(dashboard))
        result = self.build()
        self.assertEqual(result, self.build())
        item = next(item for item in result["workspaces"][0]["resources"] if item["type"] == "dashboard")
        self.assertEqual(item["files"], ["charts/derived.yaml", "charts/price.yaml", "dashboards/overview.yaml", "data/prices.csv"])
        self.assertEqual(item["sourceKinds"], ["duckdb"])
        self.assertNotIn("tags", result["workspaces"][0])
        self.assertTrue(all(resource["tags"] == [] for resource in result["workspaces"][0]["resources"]))

    def test_cross_workspace_refs_and_missing_files_are_rejected(self):
        for ref in ["../other/charts/price.yaml#/dataset", "other/price.yaml#/dataset", "missing.yaml#/dataset"]:
            with self.subTest(ref=ref):
                self.chart["dataset"] = {"id": "prices", "ref": ref}
                self.write_chart("price", self.chart)
                with self.assertRaises(ValueError):
                    self.build()

    def test_cross_workspace_dashboard_is_rejected(self):
        dashboard = {"kind": "Dashboard", "metadata": {"id": "overview", "title": "Overview"},
                     "tabs": [{"panels": [{"chart": "other/price"}]}]}
        (self.topic / "dashboards/overview.yaml").write_text(yaml.safe_dump(dashboard))
        with self.assertRaises(ValueError):
            self.build()

    def test_cycles_are_rejected(self):
        other = copy.deepcopy(self.chart)
        other["metadata"]["id"] = "other"
        other["dataset"] = {"id": "other", "ref": "price.yaml#/dataset"}
        other["chart"]["dataset"] = "other"
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
        self.assertEqual({workspace["path"] for workspace in result["workspaces"]}, {"workspaces/example", "workspaces/ftshare"})
        example = next(w for w in result["workspaces"] if w["id"] == "example")
        self.assertEqual(sum(r["type"] == "chart" for r in example["resources"]), 68)
        self.assertEqual(sum(r["type"] == "dashboard" for r in example["resources"]), 6)
        vela = next(r for r in example["resources"] if r["resourceID"] == "example_vela_dashboard")
        self.assertEqual(set(vela["files"]), {"dashboards/example_vela_dashboard.yaml", "charts/Example/Vela/example_vela_candlestick.yaml",
                                             "charts/Example/Vela/example_vela_indicators.yaml", "data/example/echarts-ohlcv.csv"})
        self.assertEqual(vela["requiredConnections"], [])
        self.assertFalse(any("health" in f["path"] for f in example["files"]))
        self.assertTrue({"workspace.yaml", "README.md"}.issubset({f["path"] for f in example["files"]}))
        self.assertFalse(any("healthkit" in r["sourceKinds"] for r in example["resources"]))
