import json, os, unittest
import render

EX = os.path.join(os.path.dirname(__file__), "..", "examples", "order-flow.json")


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


if __name__ == "__main__":
    unittest.main()
