# 메서드 분리 (Method Composition)

처음 작성할 때부터 public 메서드는 **목차**, private 메서드는 **각 장**으로 씁니다.

- public 메서드는 결과의 각 부분을 이름 있는 지역변수로 받고, 마지막 줄에서 조립만 합니다. 생성자·팩터리·다른 호출의 인자 안에서 계산하지 않습니다.
- 각 부분의 규칙(분기·기본값·포맷·문자열 조립)은 그 부분 이름의 private 메서드 하나에 둡니다. 이름은 만들어지는 값입니다(`pushTitle`, `pushBody`). 조립 메서드에 삼항·문자열 연결이 섞이지 않게 합니다.
- 이미 있는 메서드의 단순 호출은 지역변수로 받기만 하고, 그것을 감싸는 private 래퍼는 만들지 않습니다.
- 여러 부분이 쓰는 범용 헬퍼(`prefixed(prefix, separator, text)` 같은)를 먼저 만들지 않습니다. 부분마다 규칙을 그 자리에 풀어 씁니다 — 읽는 사람이 헬퍼 인자 순서를 해독하지 않아도 됩니다.
- 데이터를 꺼내는 방법은 데이터를 가진 타입의 메서드로 둡니다(`message.param(key)`). 인터페이스 static 메서드나 util 클래스에 `text(params, key)`처럼 두지 않습니다.
- 인터페이스에는 구현체가 지킬 계약만 둡니다. static·default 유틸 메서드를 두지 않습니다.
- 같은 클래스의 메서드, 특히 private 메서드를 호출할 때는 `this.`를 붙입니다. 호출하는 자리에서 이 클래스 안의 규칙이라는 것이 바로 보입니다.

```java
@Override
public PushContent push(Order order) {
    String title = this.pushTitle(order);
    String body = this.pushBody(order);
    String deepLink = this.deepLink(order);

    return new PushContent(title, body, deepLink);
}

private String pushTitle(Order order) {
    String storeName = order.param("storeName");
    return storeName.isEmpty() ? PUSH_TITLE : storeName + ", " + PUSH_TITLE;
}

private String pushBody(Order order) {
    String period = order.periodText();
    return period.isEmpty() ? PUSH_BODY : period + " · " + PUSH_BODY;
}

// Bad: 조립 자리에서 계산하고, 범용 헬퍼 인자로 규칙을 숨긴다
return new PushContent(
        prefixed(text(order.params(), "storeName"), ", ", PUSH_TITLE),
        prefixed(order.periodText(), " · ", PUSH_BODY),
        deepLink(order));
```
