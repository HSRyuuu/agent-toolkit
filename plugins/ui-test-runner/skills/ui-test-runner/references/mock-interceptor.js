// ui-test-runner — mutation 차단 인터셉터
//
// Playwright MCP는 page.route()를 직접 노출하지 않으므로,
// browser_evaluate 로 이 스크립트를 페이지에 주입한다.
// (반드시 모든 navigate 전에 매번 주입한다. 새 페이지 로드 시 자동 리셋되기 때문)
//
// 역할:
//   - window.fetch 와 XMLHttpRequest 를 가로채서
//     POST/PUT/DELETE/PATCH 요청을 백엔드에 전달하지 않고
//     가짜 성공 응답({ ok: true, mocked: true })을 즉시 반환.
//   - 가로챈 요청은 window.__uiTestMockedRequests 배열에 쌓아둠.
//   - GET, HEAD, OPTIONS 같은 read-only 요청은 그대로 통과.
//
// 시나리오에서 특정 URL/메서드에 다른 응답을 강제하고 싶으면:
//   window.__uiTestMockOverrides = [
//     { urlPattern: "/api/users", method: "POST", response: { status: 409, body: { error: "duplicate" } } }
//   ];
//   ↑ 이 배열은 인터셉터 설치 *전*에 set 해둬야 한다.

(function installMutationMock() {
  if (window.__uiTestMockInstalled) return;
  window.__uiTestMockInstalled = true;
  window.__uiTestMockedRequests = window.__uiTestMockedRequests || [];

  const MUTATION_METHODS = new Set(['POST', 'PUT', 'DELETE', 'PATCH']);
  const overrides = window.__uiTestMockOverrides || [];

  function findOverride(url, method) {
    return overrides.find((o) => {
      const methodMatch = !o.method || o.method.toUpperCase() === method.toUpperCase();
      const urlMatch = !o.urlPattern || new RegExp(o.urlPattern).test(url);
      return methodMatch && urlMatch;
    });
  }

  function defaultResponse() {
    return { status: 200, body: { ok: true, mocked: true } };
  }

  // ---- fetch override ----
  const realFetch = window.fetch.bind(window);
  window.fetch = async function patchedFetch(input, init) {
    const url = typeof input === 'string' ? input : (input && input.url) || '';
    const method = String(
      (init && init.method) || (input && input.method) || 'GET'
    ).toUpperCase();

    if (!MUTATION_METHODS.has(method)) return realFetch(input, init);

    const override = findOverride(url, method);
    const resp = override && override.response ? override.response : defaultResponse();

    window.__uiTestMockedRequests.push({
      via: 'fetch',
      method,
      url,
      mockedAt: new Date().toISOString(),
      requestBody: (init && init.body) || null,
      response: { status: resp.status, body: resp.body },
    });

    return new Response(JSON.stringify(resp.body), {
      status: resp.status,
      headers: { 'Content-Type': 'application/json' },
    });
  };

  // ---- XMLHttpRequest override ----
  const RealXHR = window.XMLHttpRequest;
  function PatchedXHR() {
    const xhr = new RealXHR();
    let _method = 'GET';
    let _url = '';
    let _reqBody = null;

    const realOpen = xhr.open.bind(xhr);
    xhr.open = function patchedOpen(method, url) {
      _method = String(method).toUpperCase();
      _url = String(url);
      return realOpen.apply(xhr, arguments);
    };

    const realSend = xhr.send.bind(xhr);
    xhr.send = function patchedSend(body) {
      _reqBody = body == null ? null : body;
      if (!MUTATION_METHODS.has(_method)) return realSend(body);

      const override = findOverride(_url, _method);
      const resp = override && override.response ? override.response : defaultResponse();
      const respText = JSON.stringify(resp.body);

      window.__uiTestMockedRequests.push({
        via: 'xhr',
        method: _method,
        url: _url,
        mockedAt: new Date().toISOString(),
        requestBody: _reqBody,
        response: { status: resp.status, body: resp.body },
      });

      setTimeout(function fulfillMocked() {
        try {
          Object.defineProperty(xhr, 'readyState', { value: 4, configurable: true });
          Object.defineProperty(xhr, 'status', { value: resp.status, configurable: true });
          Object.defineProperty(xhr, 'statusText', { value: 'OK', configurable: true });
          Object.defineProperty(xhr, 'responseText', { value: respText, configurable: true });
          Object.defineProperty(xhr, 'response', { value: respText, configurable: true });
        } catch (_) {}

        try { xhr.dispatchEvent(new ProgressEvent('readystatechange')); } catch (_) {}
        try { xhr.dispatchEvent(new ProgressEvent('load')); } catch (_) {}
        try { xhr.dispatchEvent(new ProgressEvent('loadend')); } catch (_) {}
        if (typeof xhr.onreadystatechange === 'function') xhr.onreadystatechange();
        if (typeof xhr.onload === 'function') xhr.onload();
        if (typeof xhr.onloadend === 'function') xhr.onloadend();
      }, 0);
    };

    return xhr;
  }
  PatchedXHR.prototype = RealXHR.prototype;
  window.XMLHttpRequest = PatchedXHR;

  console.log('[ui-test-runner] mutation mock installed (POST/PUT/DELETE/PATCH blocked)');
})();
