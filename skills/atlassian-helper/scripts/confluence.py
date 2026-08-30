#!/usr/bin/env python3
"""Confluence page read + write. Modify/delete is restricted to pages I authored."""

from __future__ import annotations

import argparse
import re
from typing import Any

from atlassian_common import (
    CONTENT_PATH,
    CQL_SEARCH_PATH,
    DEFAULT_LIMIT,
    MAX_LIMIT,
    PAGES_PATH,
    SPACES_PATH,
    UPLOAD_MAX_TIME_SECONDS,
    AtlassianHelperError,
    add_profile_arg,
    api_request,
    assert_owner,
    confirm_destructive,
    cql_quote,
    cql_time_value,
    file_form,
    format_timestamp,
    human_size,
    load_profile,
    my_account_id,
    prepare_upload,
    print_response,
    read_body,
    run_main,
    site_url,
    storage_to_text,
    text_to_storage,
    truncate_text,
    validate_id,
    validate_space_key,
)


def _limit(value: int | None) -> int:
    limit = DEFAULT_LIMIT if value is None else value
    if limit < 1 or limit > MAX_LIMIT:
        raise AtlassianHelperError(f"--limit은 1부터 {MAX_LIMIT} 사이여야 합니다.")
    return limit


def _page_url(profile: dict[str, Any], page: dict[str, Any]) -> str:
    links = page.get("_links") if isinstance(page, dict) else {}
    webui = links.get("webui") if isinstance(links, dict) else ""
    if webui:
        return f"{site_url(profile)}/wiki{webui}"
    return f"{site_url(profile)}/wiki/pages/viewpage.action?pageId={page.get('id')}"


def _user_name(profile: dict[str, Any], account_id: str) -> str:
    try:
        response = api_request(
            profile, "/wiki/rest/api/user", query={"accountId": account_id}
        )
    except AtlassianHelperError:
        return ""
    if not isinstance(response, dict):
        return ""
    return str(response.get("publicName") or response.get("displayName") or "")


def _get_page(profile: dict[str, Any], page_id: str, *, body: bool = True) -> dict[str, Any]:
    query = {"body-format": "storage"} if body else None
    response = api_request(profile, f"{PAGES_PATH}/{page_id}", query=query)
    if not isinstance(response, dict):
        raise AtlassianHelperError(f"예상하지 못한 응답: {response}")
    return response


def _assert_page_owner(profile: dict[str, Any], page: dict[str, Any]) -> None:
    owner = str(page.get("authorId") or "")
    name = ""
    if owner and owner != my_account_id(profile):
        name = _user_name(profile, owner)
    assert_owner(profile, owner, name, f"페이지 {page.get('id')} ({page.get('title')})")


def _space_id(profile: dict[str, Any], space_key: str) -> str:
    response = api_request(profile, SPACES_PATH, query={"keys": space_key, "limit": 1})
    results = response.get("results") if isinstance(response, dict) else []
    results = results if isinstance(results, list) else []
    for space in results:
        if isinstance(space, dict) and space.get("id"):
            return str(space["id"])
    raise AtlassianHelperError(f"스페이스를 찾을 수 없습니다: {space_key}")


def command_search(args: argparse.Namespace) -> int:
    keyword = " ".join(args.keyword or []).strip()
    clauses = [] if args.type in ("all", "") else [f"type = {args.type}"]
    if keyword:
        clauses.append(f"text ~ {cql_quote(keyword)}")
    if args.space:
        clauses.append(f"space = {cql_quote(validate_space_key(args.space))}")
    if args.title:
        clauses.append(f"title ~ {cql_quote(args.title)}")
    if args.mine:
        clauses.append("creator = currentUser()")
    if args.updated_from:
        clauses.append(f"lastmodified >= {cql_time_value(args.updated_from)}")
    if args.cql_and:
        clauses.append(f"({args.cql_and})")
    if not keyword and not args.title and not args.space and not args.mine:
        raise AtlassianHelperError("검색어나 --space/--title/--mine 중 하나는 지정하세요.")
    cql = " AND ".join(clauses) + f" ORDER BY {args.order}"
    _, profile = load_profile(args.profile)
    response = api_request(
        profile, CQL_SEARCH_PATH, query={"cql": cql, "limit": _limit(args.limit)}
    )
    if args.raw:
        return print_response(response)
    print(f"# cql: {cql}")
    results = response.get("results") if isinstance(response, dict) else []
    results = results if isinstance(results, list) else []
    if not results:
        print("(no pages)")
        return 0
    for result in results:
        if not isinstance(result, dict):
            continue
        content = result.get("content") if isinstance(result.get("content"), dict) else {}
        space = content.get("space") if isinstance(content.get("space"), dict) else {}
        container = result.get("resultGlobalContainer")
        space_name = space.get("key") or (
            container.get("title") if isinstance(container, dict) else None
        )
        updated = format_timestamp(result.get("lastModified"), args.tz)
        print(
            f"\n{content.get('id') or '-'}  [{space_name or '-'}]  {result.get('title')}"
            f"  updated={updated}"
        )
        excerpt = storage_to_text(result.get("excerpt"), limit=200)
        if excerpt:
            print(f"  {truncate_text(excerpt, 200)}")
    return 0


def command_page(args: argparse.Namespace) -> int:
    page_id = validate_id(args.id, "페이지 ID")
    _, profile = load_profile(args.profile)
    page = _get_page(profile, page_id)
    if args.raw:
        return print_response(page)
    version = page.get("version") if isinstance(page.get("version"), dict) else {}
    body = page.get("body") if isinstance(page.get("body"), dict) else {}
    storage = body.get("storage") if isinstance(body.get("storage"), dict) else {}
    print(f"{page.get('id')}  {page.get('title')}  [{page.get('status')}]")
    print(
        f"  spaceId={page.get('spaceId')} version={version.get('number')} "
        f"updated={format_timestamp(version.get('createdAt'), args.tz)}"
    )
    print(f"  url={_page_url(profile, page)}")
    if args.storage:
        print("\n## body (storage)")
        print(storage.get("value") or "")
    else:
        print("\n## body")
        print(storage_to_text(storage.get("value"), limit=args.body_limit))
    if args.comments:
        comments = api_request(
            profile,
            f"{PAGES_PATH}/{page_id}/footer-comments",
            query={"body-format": "storage", "limit": args.comments, "sort": "-created-date"},
        )
        items = comments.get("results") if isinstance(comments, dict) else []
        items = items if isinstance(items, list) else []
        print(f"\n## comments ({len(items)}건)")
        for comment in items:
            if not isinstance(comment, dict):
                continue
            comment_version = comment.get("version") or {}
            comment_body = comment.get("body") or {}
            comment_storage = comment_body.get("storage") or {}
            created = format_timestamp(
                comment_version.get("createdAt") if isinstance(comment_version, dict) else None,
                args.tz,
            )
            print(f"\n[id={comment.get('id')}] [{created}]")
            print(storage_to_text(comment_storage.get("value"), limit=400))
    return 0


def command_spaces(args: argparse.Namespace) -> int:
    _, profile = load_profile(args.profile)
    response = api_request(profile, SPACES_PATH, query={"limit": 50})
    if args.raw:
        return print_response(response)
    results = response.get("results") if isinstance(response, dict) else []
    results = results if isinstance(results, list) else []
    needle = (args.query or "").lower()
    shown = 0
    for space in results:
        if not isinstance(space, dict):
            continue
        label = f"{space.get('key')}  {space.get('name')}  (id={space.get('id')})"
        if needle and needle not in label.lower():
            continue
        print(label)
        shown += 1
    if not shown:
        print("(no spaces)")
    return 0


def command_create(args: argparse.Namespace) -> int:
    space_key = validate_space_key(args.space)
    title = (args.title or "").strip()
    if not title:
        raise AtlassianHelperError("--title은 필수입니다.")
    _, profile = load_profile(args.profile)
    body_text = read_body(args.body, args.body_file)
    payload: dict[str, Any] = {
        "spaceId": _space_id(profile, space_key),
        "status": "current",
        "title": title,
        "body": {
            "representation": "storage",
            "value": body_text if args.storage else text_to_storage(body_text),
        },
    }
    if args.parent:
        payload["parentId"] = validate_id(args.parent, "상위 페이지 ID")
    response = api_request(profile, PAGES_PATH, http_method="POST", payload=payload)
    if args.raw:
        return print_response(response)
    print(f"created page {response.get('id')}  {_page_url(profile, response)}")
    return 0


def command_update(args: argparse.Namespace) -> int:
    page_id = validate_id(args.id, "페이지 ID")
    if args.title is None and args.body is None and args.body_file is None:
        raise AtlassianHelperError("수정할 내용이 없습니다 (--title 또는 --body/--body-file).")
    _, profile = load_profile(args.profile)
    page = _get_page(profile, page_id)
    _assert_page_owner(profile, page)
    version = page.get("version") if isinstance(page.get("version"), dict) else {}
    try:
        next_version = int(version.get("number") or 0) + 1
    except (TypeError, ValueError) as exc:
        raise AtlassianHelperError(f"페이지 버전을 읽을 수 없습니다: {version}") from exc
    body = page.get("body") if isinstance(page.get("body"), dict) else {}
    storage = body.get("storage") if isinstance(body.get("storage"), dict) else {}
    if args.body is not None or args.body_file is not None:
        body_text = read_body(args.body, args.body_file)
        value = body_text if args.storage else text_to_storage(body_text)
    else:
        value = storage.get("value") or ""
    payload = {
        "id": page_id,
        "status": "current",
        "title": args.title if args.title is not None else page.get("title"),
        "body": {"representation": "storage", "value": value},
        "version": {"number": next_version, "message": args.message or "atlassian-helper update"},
    }
    response = api_request(
        profile, f"{PAGES_PATH}/{page_id}", http_method="PUT", payload=payload
    )
    print(f"updated page {page_id} (v{next_version})  {_page_url(profile, response)}")
    return 0


def command_delete(args: argparse.Namespace) -> int:
    page_id = validate_id(args.id, "페이지 ID")
    confirm_destructive(args.yes, f"페이지 {page_id}")
    _, profile = load_profile(args.profile)
    page = _get_page(profile, page_id, body=False)
    _assert_page_owner(profile, page)
    api_request(profile, f"{PAGES_PATH}/{page_id}", http_method="DELETE")
    print(f"deleted page {page_id} ({page.get('title')})")
    return 0


def _list_attachments(profile: dict[str, Any], page_id: str) -> list[dict[str, Any]]:
    response = api_request(
        profile,
        f"{CONTENT_PATH}/{page_id}/child/attachment",
        query={"expand": "version,extensions", "limit": 100},
    )
    results = response.get("results") if isinstance(response, dict) else []
    return [item for item in (results or []) if isinstance(item, dict)]


def _attachment_version(attachment: dict[str, Any]) -> int:
    version = attachment.get("version") if isinstance(attachment.get("version"), dict) else {}
    try:
        return int(version.get("number") or 0)
    except (TypeError, ValueError):
        return 0


def _repin_attachment(storage: str, filename: str, version: int) -> tuple[str, int]:
    """Point <ri:attachment ri:version-at-save> at the freshly uploaded version.

    Confluence renders the pinned version, so a replaced file stays invisible
    until the page body is re-saved with the new number.
    """
    pattern = re.compile(
        r'(<ri:attachment\b[^>]*?ri:filename="' + re.escape(filename) + r'"[^>]*?'
        r'ri:version-at-save=")(\d+)(")'
    )
    replaced = 0

    def sub(match: re.Match[str]) -> str:
        nonlocal replaced
        if int(match.group(2)) == version:
            return match.group(0)
        replaced += 1
        return f"{match.group(1)}{version}{match.group(3)}"

    return pattern.sub(sub, storage), replaced


def command_attachments(args: argparse.Namespace) -> int:
    page_id = validate_id(args.id, "페이지 ID")
    _, profile = load_profile(args.profile)
    attachments = _list_attachments(profile, page_id)
    if args.raw:
        return print_response(attachments)
    if not attachments:
        print("(no attachments)")
        return 0
    for attachment in attachments:
        extensions = (
            attachment.get("extensions")
            if isinstance(attachment.get("extensions"), dict)
            else {}
        )
        print(
            f"{attachment.get('id')}  {attachment.get('title')}  "
            f"v{_attachment_version(attachment)}  {human_size(extensions.get('fileSize'))}"
        )
    return 0


def command_attach(args: argparse.Namespace) -> int:
    page_id = validate_id(args.id, "페이지 ID")
    path, filename = prepare_upload(args.file, args.name)
    _, profile = load_profile(args.profile)
    existing = next(
        (item for item in _list_attachments(profile, page_id) if item.get("title") == filename),
        None,
    )
    if existing and not args.replace:
        raise AtlassianHelperError(
            f"같은 이름의 첨부가 이미 있습니다 (v{_attachment_version(existing)}): {filename}\n"
            "새 버전으로 교체하려면 --replace, 다른 이름으로 올리려면 --name을 쓰세요."
        )

    form = file_form(path, filename)
    form_string = [f"comment={args.comment}"] if args.comment else []
    page: dict[str, Any] = {"id": page_id}
    if existing:
        page = _get_page(profile, page_id)
        _assert_page_owner(profile, page)
        response = api_request(
            profile,
            f"{CONTENT_PATH}/{page_id}/child/attachment/{existing.get('id')}/data",
            http_method="POST",
            form=form,
            form_string=form_string,
            max_time=UPLOAD_MAX_TIME_SECONDS,
        )
    else:
        form_string.append("minorEdit=true")
        response = api_request(
            profile,
            f"{CONTENT_PATH}/{page_id}/child/attachment",
            http_method="POST",
            form=form,
            form_string=form_string,
            max_time=UPLOAD_MAX_TIME_SECONDS,
        )
        results = response.get("results") if isinstance(response, dict) else None
        if isinstance(results, list) and results and isinstance(results[0], dict):
            response = results[0]
    if args.raw:
        return print_response(response)

    version = _attachment_version(response) if isinstance(response, dict) else 0
    action = "replaced" if existing else "uploaded"
    attachment_id = response.get("id") if isinstance(response, dict) else "-"
    print(
        f"{action} attachment {filename} (v{version}, id={attachment_id}, "
        f"{human_size(path.stat().st_size)}) on page {page_id}"
    )

    if existing:
        body = page.get("body") if isinstance(page.get("body"), dict) else {}
        storage = body.get("storage") if isinstance(body.get("storage"), dict) else {}
        value = storage.get("value") or ""
        repinned, count = _repin_attachment(value, filename, version)
        if count:
            page_version = page.get("version") if isinstance(page.get("version"), dict) else {}
            next_version = int(page_version.get("number") or 0) + 1
            api_request(
                profile,
                f"{PAGES_PATH}/{page_id}",
                http_method="PUT",
                payload={
                    "id": page_id,
                    "status": "current",
                    "title": page.get("title"),
                    "body": {"representation": "storage", "value": repinned},
                    "version": {
                        "number": next_version,
                        "message": f"{filename} v{version} 반영",
                    },
                },
            )
            print(f"  본문의 ri:version-at-save {count}곳을 v{version}로 갱신 (page v{next_version})")
    else:
        print(
            "  본문에 이미지로 넣으려면 update --storage 로 다음 조각을 삽입하세요:\n"
            f'  <ac:image ac:align="center"><ri:attachment ri:filename="{filename}" '
            f'ri:version-at-save="{version}" /></ac:image>'
        )
    print(f"  {_page_url(profile, page)}")
    return 0


def command_comment(args: argparse.Namespace) -> int:
    page_id = validate_id(args.id, "페이지 ID")
    _, profile = load_profile(args.profile)
    body_text = read_body(args.body, args.body_file, label="코멘트")
    if not body_text.strip():
        raise AtlassianHelperError("코멘트 본문이 비어 있습니다.")
    response = api_request(
        profile,
        "/wiki/api/v2/footer-comments",
        http_method="POST",
        payload={
            "pageId": page_id,
            "body": {
                "representation": "storage",
                "value": body_text if args.storage else text_to_storage(body_text),
            },
        },
    )
    if args.raw:
        return print_response(response)
    print(f"commented on page {page_id} (id={response.get('id')})")
    return 0


def add_body_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--body", help="본문 텍스트 (빈 줄=문단, '- '=목록, '# '=제목)")
    parser.add_argument("--body-file", help="본문 파일 경로 ('-'는 stdin)")
    parser.add_argument(
        "--storage", action="store_true", help="본문을 Confluence storage XHTML 그대로 전달"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Confluence page read/write")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Search pages with CQL filters")
    add_profile_arg(search)
    search.add_argument("keyword", nargs="*", help="본문/제목 검색어")
    search.add_argument("--space", help="space key")
    search.add_argument("--title", help="제목 부분 일치")
    search.add_argument("--mine", action="store_true", help="creator = currentUser()")
    search.add_argument(
        "--type",
        default="page",
        help='content type (default "page"). "folder"는 폴더만, "all"은 타입 제한 없이 검색',
    )
    search.add_argument("--updated-from", help='예: "2026-07-01"')
    search.add_argument("--and", dest="cql_and", help="추가 CQL 조건")
    search.add_argument("--order", default="lastmodified DESC")
    search.add_argument("--limit", type=int)
    search.add_argument("--tz", default="Asia/Seoul")
    search.add_argument("--raw", action="store_true")
    search.set_defaults(func=command_search)

    page = subparsers.add_parser("page", help="Page detail (+ optional comments)")
    add_profile_arg(page)
    page.add_argument("id", help="페이지 ID (숫자)")
    page.add_argument("--body-limit", type=int, default=4000)
    page.add_argument("--storage", action="store_true", help="본문을 storage XHTML 원문으로 출력")
    page.add_argument("--comments", type=int, default=0, help="코멘트 N건 표시")
    page.add_argument("--tz", default="Asia/Seoul")
    page.add_argument("--raw", action="store_true")
    page.set_defaults(func=command_page)

    spaces = subparsers.add_parser("spaces", help="List spaces")
    add_profile_arg(spaces)
    spaces.add_argument("--query", help="키/이름 부분 일치 필터")
    spaces.add_argument("--raw", action="store_true")
    spaces.set_defaults(func=command_spaces)

    create = subparsers.add_parser("create", help="Create a page (안전 작업)")
    add_profile_arg(create)
    create.add_argument("--space", required=True, help="space key")
    create.add_argument("--title", required=True)
    add_body_args(create)
    create.add_argument("--parent", help="상위 페이지 ID")
    create.add_argument("--raw", action="store_true")
    create.set_defaults(func=command_create)

    update = subparsers.add_parser("update", help="Update a page I created (작성자 확인)")
    add_profile_arg(update)
    update.add_argument("id")
    update.add_argument("--title")
    add_body_args(update)
    update.add_argument("--message", help="버전 코멘트")
    update.set_defaults(func=command_update)

    delete = subparsers.add_parser("delete", help="Delete a page I created (작성자 확인 + --yes)")
    add_profile_arg(delete)
    delete.add_argument("id")
    delete.add_argument("--yes", action="store_true", help="삭제 확인 (필수)")
    delete.set_defaults(func=command_delete)

    attachments = subparsers.add_parser("attachments", help="List page attachments")
    add_profile_arg(attachments)
    attachments.add_argument("id", help="페이지 ID (숫자)")
    attachments.add_argument("--raw", action="store_true")
    attachments.set_defaults(func=command_attachments)

    attach = subparsers.add_parser(
        "attach", help="Upload a file/image to a page (교체는 작성자 확인)"
    )
    add_profile_arg(attach)
    attach.add_argument("id", help="페이지 ID (숫자)")
    attach.add_argument("--file", required=True, help="업로드할 로컬 파일 경로")
    attach.add_argument("--name", help="첨부 파일명 (기본: 원본 파일명)")
    attach.add_argument(
        "--replace", action="store_true", help="같은 이름 첨부를 새 버전으로 교체 (작성자 확인)"
    )
    attach.add_argument("--comment", help="첨부 설명")
    attach.add_argument("--raw", action="store_true")
    attach.set_defaults(func=command_attach)

    comment = subparsers.add_parser("comment", help="Add a footer comment (안전 작업)")
    add_profile_arg(comment)
    comment.add_argument("id")
    add_body_args(comment)
    comment.add_argument("--raw", action="store_true")
    comment.set_defaults(func=command_comment)

    return parser


def main() -> int:
    return run_main(build_parser)


if __name__ == "__main__":
    raise SystemExit(main())
