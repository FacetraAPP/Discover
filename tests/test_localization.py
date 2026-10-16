import copy
from pathlib import Path
import shutil
import re
import tempfile
import unittest

import yaml

from scripts import build_catalog as catalog
from scripts import validate_yaml as validation

ROOT = Path(__file__).resolve().parents[1]


class LocalizationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.topic = self.root / "workspaces/sales"
        shutil.copytree(ROOT / "docs/starter", self.topic)
        self.chart_path = self.topic / "charts/sales.yaml"
        self.chart = validation.load_yaml(self.chart_path.read_bytes(), "chart")
        self.chart["i18n"] = {"defaultLocale": "zh-Hans", "messages": {
            "title": {"zh-Hans": "销售额", "en": "Sales"},
            "notes": {"zh-Hans": "虚构数据", "en": "Fictional data"},
            "threshold": {"zh-Hans": "最低收入", "en": "Minimum revenue"}}}
        self.chart["metadata"].update(title={"i18n": "title"}, notes={"i18n": "notes"})
        self.chart["params"][0]["label"] = {"i18n": "threshold"}

    def build(self):
        self.chart_path.write_text(yaml.safe_dump(self.chart, allow_unicode=True))
        return catalog.build_catalog(self.root, "a" * 40)

    def test_catalog_resolves_default_language_without_rewriting_downloads(self):
        before = copy.deepcopy(self.chart)
        workspace = self.build()["workspaces"][0]
        chart = next(item for item in workspace["resources"] if item["resourceID"] == "sales")
        self.assertEqual((chart["title"], chart["description"]), ("销售额", "虚构数据"))
        self.assertEqual(validation.load_yaml(self.chart_path.read_bytes(), "chart"), before)
        self.chart["i18n"]["defaultLocale"] = "EN"
        chart = next(item for item in self.build()["workspaces"][0]["resources"] if item["resourceID"] == "sales")
        self.assertEqual((chart["title"], chart["description"]), ("Sales", "Fictional data"))

    def test_invalid_catalogs_and_unknown_keys_fail_with_file_context(self):
        invalid = [None, [], {}, {"defaultLocale": "zh_Hans", "messages": {}},
                   {"defaultLocale": "en", "messages": {"title": {"zh-Hans": "标题"}}},
                   {"defaultLocale": "en", "messages": {"title": {"en": "Title", "EN": "Duplicate"}}},
                   {"defaultLocale": "en", "messages": {"title": {"en": " "}}},
                   {"defaultLocale": "en", "messages": {"bad/key": {"en": "Title"}}}]
        original = copy.deepcopy(self.chart)
        for value in invalid:
            self.chart = copy.deepcopy(original)
            self.chart["i18n"] = value
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "sales/charts/sales.yaml"):
                self.build()
        for value in [{"i18n": "unknown"}, {"i18n": "title", "typo": True}, {"i18n": 12}]:
            self.chart = copy.deepcopy(original)
            self.chart["metadata"]["title"] = value
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "metadata.title"):
                self.build()

    def test_dashboard_and_option_references_use_their_own_catalog(self):
        dashboard_path = self.topic / "dashboards/overview.yaml"
        dashboard = validation.load_yaml(dashboard_path.read_bytes(), "dashboard")
        dashboard["i18n"] = {"defaultLocale": "en", "messages": {
            "title": {"en": "Overview", "zh-Hans": "概览"}}}
        dashboard["metadata"]["title"] = {"i18n": "title"}
        dashboard["tabs"][0]["title"] = {"i18n": "title"}
        dashboard_path.write_text(yaml.safe_dump(dashboard))
        resources = self.build()["workspaces"][0]["resources"]
        self.assertEqual(next(item for item in resources if item["type"] == "dashboard")["title"], "Overview")
        dashboard["metadata"]["title"] = {"i18n": "notes"}
        dashboard_path.write_text(yaml.safe_dump(dashboard))
        with self.assertRaisesRegex(ValueError, "resource-local i18n message"):
            self.build()
        dashboard["metadata"]["title"] = {"i18n": "title"}
        dashboard_path.write_text(yaml.safe_dump(dashboard))
        self.chart["chart"] = {"dataset": self.chart["dataset"]["id"], "renderer": "echarts", "option": {
            "title": {"text": {"i18n": "title"}}, "series": [{"name": {"i18n": "notes"}, "type": "bar"}]}}
        self.build()
        self.chart["chart"]["option"]["series"][0]["name"] = {"i18n": "unknown"}
        with self.assertRaisesRegex(ValueError, r"chart.option.series\[0\].name"):
            self.build()

    def test_source_data_and_translated_script_prefixes_stay_authored_text(self):
        self.chart["i18n"]["messages"]["notes"]["en"] = "js: this is text"
        self.chart["sources"]["remote"] = {"source": "http", "method": "post", "url": "https://example.com", "json": {"i18n": "raw request data"}}
        self.build()
        self.assertEqual(self.chart["sources"]["remote"]["json"], {"i18n": "raw request data"})
        self.assertEqual(self.chart["i18n"]["messages"]["notes"]["en"], "js: this is text")

    def test_every_example_resource_has_complete_english_and_chinese_display_text(self):
        folder = ROOT / "workspaces/example"
        paths = [*folder.glob("charts/**/*.yaml"), *folder.glob("dashboards/**/*.yaml")]
        self.assertTrue(paths)
        for path in paths:
            document = validation.load_yaml(path.read_bytes(), str(path))
            with self.subTest(resource=path.stem):
                self.assertEqual(document["i18n"]["defaultLocale"], "zh-Hans")
                self.assertIsInstance(document["metadata"]["title"], dict)
                for translations in document["i18n"]["messages"].values():
                    self.assertEqual(set(translations), {"zh-Hans", "en"})
                    self.assertTrue(all(text.strip() for text in translations.values()))
                for parameter in document.get("params", []):
                    self.assertIsInstance(parameter["label"], dict)
                for tab in document.get("tabs", []):
                    self.assertIsInstance(tab["title"], dict)

    def test_example_options_have_no_hard_coded_chinese_display_strings(self):
        def check(value, path):
            if isinstance(value, dict):
                if "i18n" in value or "from" in value:
                    return
                for key, child in value.items():
                    check(child, path + "." + key)
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    check(child, f"{path}[{index}]")
            elif isinstance(value, str):
                self.assertIsNone(re.search("[\u4e00-\u9fff]", value), path)
        for path in (ROOT / "workspaces/example/charts").rglob("*.yaml"):
            document = validation.load_yaml(path.read_bytes(), str(path))
            check(document["chart"].get("option"), str(path))

    def test_authored_example_legends_match_their_translated_series_or_items(self):
        for path in (ROOT / "workspaces/example/charts").rglob("*.yaml"):
            document = validation.load_yaml(path.read_bytes(), str(path))
            option = document["chart"].get("option", {})
            entries = option.get("legend", {}).get("data", [])
            if not entries:
                continue
            for language in ["en", "zh-Hans"]:
                def resolve(value):
                    return document["i18n"]["messages"][value["i18n"]][language] if isinstance(value, dict) else value
                names = set()
                for series in option.get("series", []):
                    if "name" in series:
                        names.add(resolve(series["name"]))
                    data = series.get("data", [])
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and "name" in item:
                                names.add(resolve(item["name"]))
                            elif series.get("type") == "themeRiver":
                                names.add(resolve(item[2]))
                for entry in entries:
                    with self.subTest(resource=path.stem, language=language):
                        self.assertIn(resolve(entry), names)
