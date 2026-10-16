"""collect.py 의 Java 파서 최소 검증. 실행: python3 test_collect.py"""
from collect import parse_java

SRC = '''
@RestController
@RequestMapping(value = "/api/foo")
public class FooController implements Api {
    private final Runnable r = () -> { run(); };
    static { init(); }

    @GetMapping("/{id}")
    public Foo get(@PathVariable("id") Long id, final Map<String, List<Long>> m) {
        if (id == null) { return null; }
        String s = "{ not a block }"; // {
        return service.find(id);
    }

    @KafkaListener(topics = "foo-topic", groupId = "g")
    public void consume(String msg) { service.handle(msg); }

    abstract void noBody(int a);

    class Inner { void deep() {} }
}
'''

classes, methods = parse_java(SRC)
by = {m["key"]: m for m in methods}
assert [c["name"] for c in classes] == ["FooController", "FooController.Inner"], classes
assert classes[0]["supers"] == ["Api"]
assert set(by) == {"get(Long, Map<String, List<Long>>)", "consume(String)", "noBody(int)", "deep()"}, by.keys()
assert by["get(Long, Map<String, List<Long>>)"]["endpoint"]["label"] == "GET /api/foo/{id}"
assert by["consume(String)"]["endpoint"]["kind"] == "KAFKA"
assert by["deep()"]["cls"] == "FooController.Inner"
g = by["get(Long, Map<String, List<Long>>)"]
assert (g["start"], g["end"]) == (8, 13), (g["start"], g["end"])
print("ok")
