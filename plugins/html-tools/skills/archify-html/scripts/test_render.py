import json, os, unittest
import render

EX = os.path.join(os.path.dirname(__file__), "..", "examples", "order-flow.json")
DM = os.path.join(os.path.dirname(__file__), "..", "examples", "data-model-example.json")
TABS_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")
TABS = os.path.join(TABS_DIR, "tabs-example.json")


def load():
    with open(EX, encoding="utf-8") as f:
        return json.load(f)


class RenderTest(unittest.TestCase):
    def test_example_is_valid(self):
        errors, warns = render.validate(load())
        self.assertEqual((errors, warns), ([], []))

    def test_rejects_bad_edge_and_op(self):
        d = load()
        d["edges"].append({"n": "9", "from": "nope", "to": "o_cart"})
        d["groups"][1]["nodes"][0]["db"][0]["op"] = "X"
        errors, _ = render.validate(d)
        self.assertEqual(len(errors), 2)

    def test_build_embeds_ver_and_escapes_script_end(self):
        d = load()
        d["groups"][0]["nodes"][0]["desc"] = "</script><b>"
        html = render.build(d, "2026-01-02")
        self.assertIn('"ver": "2026-01-02"', html)
        self.assertEqual(html.count("</script>"), 1)  # 템플릿의 닫는 태그 하나뿐

    def test_agent_text_is_static_and_flow_only(self):
        d = load()
        d["foot"] = [{"title": "결론", "items": ["FOOT-ONLY-MARKER"]}]
        d["groups"][0]["nodes"][0]["note"] = "a < b & c"
        text = render.agent_text(d)
        self.assertIn("storefront-web · 주문하기 → order-api · 주문 생성  [확정]", text)
        self.assertIn("[미확인]", text)
        self.assertNotIn("FOOT-ONLY-MARKER", text)  # foot 는 에이전트 텍스트에 넣지 않는다
        html = render.build(d, "2026-01-02")
        self.assertIn("a &lt; b &amp; c", html)  # 소스에 정적으로 들어가고 이스케이프된다
        self.assertEqual(html.count('id="agenttext"'), 1)
        self.assertNotIn("<!--AGENT_TEXT-->", html)

    def test_rejects_code_line_numbers_but_allows_file_names(self):
        d = load()
        d["groups"][1]["nodes"][0]["db"][0]["e"] = "CartRepository.java:41"
        d["groups"][1]["nodes"][1]["note"] = "ProductRepository.java:33-40 참고, 10:30 배치"
        errors, _ = render.validate(d)
        self.assertEqual(len(errors), 2)
        d["groups"][1]["nodes"][0]["db"][0]["e"] = "CartRepository.save"
        d["groups"][1]["nodes"][1]["note"] = "ProductRepository 참고, 10:30 배치"
        self.assertEqual(render.validate(d)[0], [])

    def test_strip_lines_handles_variants(self):
        f = render.strip_lines
        self.assertEqual(f("A.java:127-149 (tag :144), :118-125"), "A.java")
        self.assertEqual(f("A.java:85-105, :123-140, :142-150"), "A.java")
        self.assertEqual(f("A.java:30-34 (호출 :159)"), "A.java")
        self.assertEqual(f("A.java:262,364 / B.java:47-52"), "A.java / B.java")


def load_dm():
    with open(DM, encoding="utf-8") as f:
        return json.load(f)


class ZoomTest(unittest.TestCase):
    def test_architecture_map_uses_natural_width_with_zoom_controls(self):
        html = render.build(load(), "2026-01-02")
        for marker in ('id="zin"', 'id="zout"', 'id="zreset"', 'id="zfit"', "Math.round(W * zoom)"):
            self.assertIn(marker, html)
        self.assertNotIn("svg.style.minWidth", html)  # 화면 폭 기준 축소 대신 원래 크기를 쓴다


class DataModelTest(unittest.TestCase):
    def test_example_is_valid(self):
        self.assertEqual(render.validate(load_dm()), ([], []))

    def test_kind_selects_template_and_defaults_to_architecture(self):
        self.assertIn('id="map"', render.build(load(), "2026-01-02"))
        html = render.build(load_dm(), "2026-01-02")
        self.assertIn('id="sec-schema"', html)
        self.assertNotIn('id="map"', html)

    def test_unknown_kind_is_an_error(self):
        d = load_dm()
        d["kind"] = "nope"
        errors, _ = render.validate(d)
        self.assertEqual(len(errors), 1)

    def test_rejects_broken_references_and_row_widths(self):
        d = load_dm()
        d["relations"].append({"from": "nope", "to": "lot"})
        d["flows"][0]["tables"][0]["rows"][0]["c"].pop()
        d["flows"][1]["tables"][0]["rows"][0]["op"] = "bad"
        d["views"]["tabs"][0]["rows"][0]["c"].append("extra")
        d["tables"][0]["tone"] = "z"
        errors, _ = render.validate(d)
        self.assertEqual(len(errors), 5)

    def test_rejects_code_line_numbers(self):
        d = load_dm()
        d["tables"][0]["columns"][0]["d"] = "RuleRepository.java:41 참고"
        errors, _ = render.validate(d)
        self.assertEqual(len(errors), 1)

    def test_build_escapes_script_end(self):
        d = load_dm()
        d["tables"][0]["summary"] = "</script><img src=x onerror=alert(1)>"
        html = render.build(d, "2026-01-02")
        self.assertEqual(html.count("</script>"), 1)  # 템플릿의 닫는 태그 하나뿐
        self.assertIn("&lt;/script&gt;", html)  # 에이전트용 텍스트는 이스케이프된다

    def test_agent_text_is_plain_and_excludes_foot(self):
        d = load_dm()
        d["foot"] = [{"title": "꼬리", "items": ["FOOT-ONLY-MARKER"]}]
        text = render.agent_text(d)
        self.assertNotIn("FOOT-ONLY-MARKER", text)
        self.assertIn("근거: 가상 스키마", text)  # basis 는 넣는다
        self.assertIn("INSERT: id=9001, rule=10 가입 이벤트", text)
        self.assertIn("reward_rules → reward_lots  [1:N]", text)
        self.assertNotIn("**", text)  # 화면용 강조 기호는 걷어낸다
        self.assertNotIn("`", text)
        self.assertEqual(render.build(d, "2026-01-02").count('id="agenttext"'), 1)


def load_tabs_example():
    with open(TABS, encoding="utf-8") as f:
        return json.load(f)


class TabsTest(unittest.TestCase):
    def test_example_is_valid(self):
        self.assertEqual(render.validate(load_tabs_example(), TABS_DIR), ([], []))

    def test_build_has_sticky_tabbar_and_inert_templates_per_tab(self):
        html = render.build(load_tabs_example(), "2026-01-02", TABS_DIR)
        self.assertIn("position: sticky", html)
        self.assertEqual(html.count('<template id="tpl-'), 2)
        self.assertEqual(html.count('role="tab"'), 2)
        self.assertEqual(html.count('id="agenttext"'), 2)  # 각 탭의 에이전트용 텍스트가 JS 없이 소스에 있다
        self.assertEqual(html.count("</script>"), html.count("<script>"))
        self.assertIn('/*KEYS_START*/["flow", "model"]/*KEYS_END*/', html)
        for marker in ("<!--TAB_", "<!--TITLE-->"):
            self.assertNotIn(marker, html)

    def test_panel_css_is_scoped_to_the_shadow_root(self):
        css = render.to_shadow_css(':root { --a: 1; }\n@media (prefers-color-scheme: dark) {\n  :root:not([data-theme="light"]) { --a: 2; }\n}\n:root[data-theme="dark"] { --a: 2; }\nbody { margin: 0; }')
        self.assertIn(":host {", css)
        self.assertIn(':host(:not([data-theme="light"]))', css)
        self.assertIn(':host([data-theme="dark"])', css)
        self.assertIn(".pg {", css)
        self.assertNotIn(":root", css)
        self.assertNotRegex(css, r"(?m)^\s*body\s*\{")

    def test_tabs_page_does_not_leak_panel_css_into_the_document(self):
        html = render.build(load_tabs_example(), "2026-01-02", TABS_DIR)
        outer = html.split("<template", 1)[0]
        self.assertNotIn(".node", outer)  # 지도 CSS 는 템플릿 안에만 있다

    def test_agent_text_includes_every_tab(self):
        text = render.agent_text(load_tabs_example(), TABS_DIR)
        self.assertIn("탭 2개: 주문 흐름 지도, 리워드 데이터 모델", text)
        self.assertIn("storefront-web · 주문하기 → order-api · 주문 생성", text)
        self.assertIn("reward_rules → reward_lots  [1:N]", text)

    def test_inline_data_and_explicit_ids_work(self):
        d = {"kind": "tabs", "tabs": [{"id": "a", "label": "A", "data": load()}, {"id": "b", "label": "B", "data": load_dm()}]}
        self.assertEqual(render.validate(d, TABS_DIR), ([], []))
        self.assertIn('id="tab-a"', render.build(d, "2026-01-02", TABS_DIR))

    def test_rejects_broken_tabs_with_the_tab_label(self):
        base = {"kind": "tabs", "tabs": [{"label": "A", "file": "order-flow.json"}]}
        for tabs, expect in (
            ([], "tabs 가 비어"),
            ([{"label": "A", "file": "nope.json"}], "읽지 못했다"),
            ([{"label": "A", "file": "order-flow.json", "data": {"kind": "architecture"}}], "하나만"),
            ([{"label": "A"}], "하나만"),
            ([{"file": "order-flow.json"}], "label"),
            ([{"id": "x", "label": "A", "file": "order-flow.json"}, {"id": "x", "label": "B", "file": "order-flow.json"}], "중복"),
            ([{"id": "1bad", "label": "A", "file": "order-flow.json"}], "id 는"),
            ([{"label": "A", "data": {"kind": "tabs", "tabs": []}}], "tabs 를 넣을 수 없다"),
        ):
            errors, _ = render.validate({**base, "tabs": tabs}, TABS_DIR)
            self.assertTrue(any(expect in e for e in errors), (expect, errors))

    def test_child_errors_are_prefixed_with_the_tab_label(self):
        bad = load_dm()
        bad["flows"][0]["tables"][0]["rows"][0]["op"] = "bad"
        errors, _ = render.validate({"kind": "tabs", "tabs": [{"label": "모델", "data": bad}]}, TABS_DIR)
        self.assertTrue(errors and all(e.startswith("[모델] ") for e in errors))

    def test_title_and_labels_are_escaped(self):
        d = load_tabs_example()
        d["meta"]["title"] = "<b>x</b>"
        d["tabs"][0]["label"] = "<i>y</i>"
        html = render.build(d, "2026-01-02", TABS_DIR)
        self.assertIn("&lt;b&gt;x&lt;/b&gt;", html)
        self.assertIn("&lt;i&gt;y&lt;/i&gt;", html)


if __name__ == "__main__":
    unittest.main()
