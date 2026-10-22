import copy
from pathlib import Path
import unittest
from scripts import validate_yaml as v
from scripts import build_catalog as catalog
ROOT=Path(__file__).resolve().parents[1]

class HTTPCollectionTests(unittest.TestCase):
    def doc(self,source):
        return {"metadata":{"id":"collection","title":"Collection"},"sources":{"data":source},
            "dataset":{"id":"data","sources":[{"id":"raw","ref":"#/sources/data"}]},
            "chart":{"dataset":"data","renderer":"value","value":"value"}}
    def source(self,**extra): return dict(source="http",url="https://example.com",**extra)
    def test_collection_shapes_and_multiple_state_fields_are_supported(self):
        for source in [
            self.source(pagination={"initial":{"n":1},"next":"if page.n < 3 { #{n: page.n + 1} } else { () }"}),
            self.source(pagination={"initial":{"cursor":None,"time":123},"records":"response.json.items","next":"response.json.next"}),
            self.source(format="html",extract={"rows":"article","fields":{"title":{"selector":"h2"}}}),
            self.source(format="xml",extract={"rows":"/a:feed/a:entry","namespaces":{"a":"urn:atom"},"fields":{"title":{"selector":"a:title"}}}),
        ]: v.validate_chart(self.doc(source),"fixture")
    def test_collection_rejects_bad_limits_scopes_and_post_replay(self):
        for source in [
            self.source(params={"page":"{{ page.n }}"}),
            self.source(params={"id":"{{ item.id }}"}),
            self.source(foreach={"source":"missing"}),
            self.source(pagination={"initial":{},"next":"()","max_pages":0}),
            self.source(pagination={"initial":{"n":"{{ page.n }}"},"next":"()"}),
            self.source(pagination={"initial":{},"next":"()","records":"records"},recordsPath=["items"]),
            self.source(format="html"),
            self.source(limits={"max_requests":0}),
            self.source(limits={"max_bytes":104857601}),
            self.source(method="post",retry={}),
            self.source(retry={"max_attempts":True}),
            self.source(pagination={"initial":{},"next":"x"*4097}),
        ]:
            with self.subTest(source=source), self.assertRaises(ValueError): v.validate_chart(self.doc(source),"fixture")
    def test_dag_rejects_missing_duplicate_and_mixed_reference_cycles(self):
        doc=self.doc(self.source(depends_on=["missing"]))
        v.validate_chart(doc,"fixture")
        with self.assertRaisesRegex(ValueError,"missing source"): v.validate_chart_graph({"collection":doc},"fixture")
        duplicate=self.doc(self.source(depends_on=["data","data"]))
        with self.assertRaises(ValueError): v.validate_chart(duplicate,"fixture")
        doc=self.doc(self.source(depends_on=["alias"]))
        doc["sources"]["alias"]={"ref":"#/sources/data"}
        v.validate_chart(doc,"fixture")
        with self.assertRaisesRegex(ValueError,"cyclic"): v.validate_chart_graph({"collection":doc},"fixture")
    def test_each_new_recipe_is_independently_installable_and_has_bilingual_notes(self):
        example=next(w for w in catalog.build_catalog(ROOT,"a"*40)["workspaces"] if w["id"]=="example")
        for kind in ["page","offset","links","foreach","html","xml","cursor"]:
            id="example_http_"+kind
            item=next(r for r in example["resources"] if r["resourceID"]==id)
            self.assertEqual(item["sourceKinds"],["http"])
            self.assertEqual(item["files"],[item["path"]])
            self.assertEqual(item["requiredConnections"],[{"alias":"github_example","type":"key-value"}] if kind in {"cursor","links"} else [])
            doc=v.load_yaml((ROOT/"workspaces/example"/item["path"]).read_bytes(),id)
            self.assertEqual(set(doc["i18n"]["messages"]["notes"]),{"en","zh-Hans"})
