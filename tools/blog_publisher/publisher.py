"""Core import and publishing helpers for the local blog publisher."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Callable, Iterable
from urllib.parse import unquote, urlsplit

MARKDOWN_EXTENSIONS = {".md", ".mdx"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov"}
DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".txt", ".zip"}

SITE_URL_FALLBACK = "https://venterwu.github.io/"
REPO_URL_FALLBACK = "https://github.com/VenterWu/VenterWu.github.io"
DEFAULT_AUTHOR = "Kefan Wu"
DEFAULT_TAG = "notes"
PUBLIC_REFERENCE_PREFIXES = ("/uploads/", "/images/", "/files/")
PUBLIC_ROOT_REFERENCES = {"/favicon.svg", "/robots.txt"}
MARKDOWN_URL_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
HTML_MEDIA_URL_RE = re.compile(
    r"<(?:img|video|audio|source)\b[^>]*\bsrc\s*=\s*(['\"])(.*?)\1",
    re.IGNORECASE,
)

LogCallback = Callable[[str], None]


@dataclass(slots=True)
class PublishMetadata:
    title: str = ""
    slug: str = ""
    description: str = ""
    author: str = DEFAULT_AUTHOR
    date: str = ""
    time: str = ""
    tags: list[str] = field(default_factory=lambda: [DEFAULT_TAG])
    draft: bool = False
    featured: bool = False
    order: int = 100
    hero_image: str = ""


@dataclass(slots=True)
class ImportResult:
    source: Path
    destination: Path
    public_url: str
    kind: str
    message: str


@dataclass(slots=True)
class LibraryItem:
    type: str
    kind: str
    title: str
    slug: str
    relative_path: str
    public_url: str
    description: str = ""
    author: str = ""
    date: str = ""
    updated_date: str = ""
    tags: list[str] = field(default_factory=list)
    draft: bool = False
    featured: bool = False
    order: int | None = None
    hero_image: str = ""
    file_size: int = 0
    modified_time: str = ""
    references: list[str] = field(default_factory=list)
    referenced_by: list[str] = field(default_factory=list)


def find_repo_root(start: str | Path | None = None) -> Path | None:
    current = Path(start or Path.cwd()).expanduser()
    if current.is_file():
        current = current.parent
    current = current.resolve(strict=False)

    for candidate in (current, *current.parents):
        if (candidate / "package.json").is_file() and (candidate / "astro.config.ts").is_file():
            return candidate
    return None


def require_repo_root(path: str | Path) -> Path:
    root = Path(path).expanduser().resolve(strict=False)
    if not (root / "package.json").is_file() or not (root / "astro.config.ts").is_file():
        raise ValueError(f"Not an Astro repository root: {root}")
    return root


def read_default_author(repo_root: Path) -> str:
    config_path = repo_root / "src" / "utils" / "config.ts"
    if not config_path.is_file():
        return DEFAULT_AUTHOR
    text = config_path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"author\s*:\s*\{.*?name\s*:\s*['\"]([^'\"]+)", text, re.DOTALL)
    return match.group(1) if match else DEFAULT_AUTHOR


def read_site_url(repo_root: Path) -> str:
    config_path = repo_root / "src" / "utils" / "config.ts"
    if not config_path.is_file():
        return SITE_URL_FALLBACK
    text = config_path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"url\s*:\s*['\"]([^'\"]+)", text)
    return match.group(1) if match else SITE_URL_FALLBACK


def read_repo_url(repo_root: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return REPO_URL_FALLBACK

    remote = completed.stdout.strip()
    if not remote:
        return REPO_URL_FALLBACK
    if remote.startswith("git@github.com:"):
        remote = "https://github.com/" + remote.removeprefix("git@github.com:")
    if remote.endswith(".git"):
        remote = remote[:-4]
    return remote


def parse_tags(raw_tags: str | Iterable[str]) -> list[str]:
    if isinstance(raw_tags, str):
        pieces = raw_tags.split(",")
    else:
        pieces = list(raw_tags)
    tags = [str(tag).strip() for tag in pieces if str(tag).strip()]
    return tags or [DEFAULT_TAG]


def slugify(value: str, fallback: str = "untitled") -> str:
    normalized = value.strip().lower().replace("_", "-")
    normalized = re.sub(r"\s+", "-", normalized)
    normalized = re.sub(r"[^\w.-]+", "-", normalized, flags=re.UNICODE)
    normalized = re.sub(r"-+", "-", normalized).strip("-.")
    return normalized or fallback


def guess_title_from_path(path: Path) -> str:
    words = re.sub(r"[-_]+", " ", path.stem).strip()
    return words.title() if words else "Untitled"


def split_frontmatter(text: str) -> tuple[str, str]:
    match = re.match(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", text, re.DOTALL)
    if not match:
        return "", text
    return match.group(1), text[match.end() :]


def parse_frontmatter(frontmatter: str) -> dict[str, object]:
    data: dict[str, object] = {}
    current_list_key: str | None = None

    for raw_line in frontmatter.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if current_list_key and stripped.startswith("- "):
            current_value = data.setdefault(current_list_key, [])
            if isinstance(current_value, list):
                current_value.append(_parse_scalar(stripped[2:].strip()))
            continue

        current_list_key = None
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not value:
            data[key] = []
            current_list_key = key
            continue
        data[key] = _parse_scalar(value)

    return data


def read_markdown_metadata(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    frontmatter, _body = split_frontmatter(text)
    return parse_frontmatter(frontmatter) if frontmatter else {}


def scan_content_library(repo_root: Path) -> list[LibraryItem]:
    repo_root = require_repo_root(repo_root)
    asset_items = _scan_public_assets(repo_root)
    known_public_urls = {item.public_url for item in asset_items if item.public_url}

    markdown_items: list[LibraryItem] = []
    for collection in ("blog", "pages"):
        collection_root = repo_root / "src" / "content" / collection
        if not collection_root.is_dir():
            continue
        for path in sorted(collection_root.rglob("*.md")):
            if path.is_file():
                markdown_items.append(_read_markdown_library_item(repo_root, path, collection, known_public_urls))

    _attach_reverse_references(markdown_items, asset_items)
    return sorted([*markdown_items, *asset_items], key=_library_sort_key)


def save_markdown_metadata(repo_root: Path, relative_path: str | Path, metadata: PublishMetadata) -> Path:
    repo_root = require_repo_root(repo_root)
    raw_path = Path(relative_path)
    path = raw_path if raw_path.is_absolute() else repo_root / raw_path
    path = path.resolve(strict=False)
    collection = _markdown_collection_for_path(repo_root, path)
    if not path.is_file():
        raise ValueError(f"Markdown file does not exist: {path}")
    if path.suffix.lower() not in MARKDOWN_EXTENSIONS:
        raise ValueError(f"Selected item is not a Markdown file: {path}")

    validate_metadata(collection, metadata)

    text = path.read_text(encoding="utf-8-sig", errors="replace")
    frontmatter, body = split_frontmatter(text)
    existing = parse_frontmatter(frontmatter) if frontmatter else {}
    updated = dict(existing)

    updated["title"] = metadata.title.strip()
    updated["description"] = metadata.description.strip()

    if collection == "blog":
        updated["pubDate"] = format_datetime(metadata.date, metadata.time)
        updated["author"] = metadata.author.strip()
        updated["tags"] = parse_tags(metadata.tags)
        if metadata.hero_image.strip():
            updated["heroImage"] = metadata.hero_image.strip()
        else:
            updated.pop("heroImage", None)
        updated["draft"] = bool(metadata.draft)
        updated["featured"] = bool(metadata.featured)
        preferred_keys = [
            "title",
            "description",
            "pubDate",
            "updatedDate",
            "author",
            "tags",
            "heroImage",
            "draft",
            "featured",
        ]
    else:
        if metadata.date.strip():
            updated["updatedDate"] = format_datetime(metadata.date, metadata.time)
        else:
            updated.pop("updatedDate", None)
        updated["order"] = int(metadata.order)
        updated["draft"] = bool(metadata.draft)
        preferred_keys = ["title", "description", "updatedDate", "order", "draft"]

    frontmatter_output = serialize_frontmatter(updated, preferred_keys)
    path.write_text(f"{frontmatter_output}\n\n{body.rstrip()}\n", encoding="utf-8", newline="\n")
    return path


def serialize_frontmatter(data: dict[str, object], preferred_keys: Iterable[str]) -> str:
    lines = ["---"]
    written: set[str] = set()

    for key in preferred_keys:
        if key in data and _should_write_frontmatter_value(key, data[key]):
            lines.extend(_frontmatter_value_lines(key, data[key]))
            written.add(key)

    for key in sorted(data):
        if key not in written and _should_write_frontmatter_value(key, data[key]):
            lines.extend(_frontmatter_value_lines(key, data[key]))

    lines.append("---")
    return "\n".join(lines)


def extract_public_references(
    markdown_body: str,
    hero_image: str = "",
    known_public_urls: Iterable[str] | None = None,
) -> list[str]:
    known_urls = set(known_public_urls or ())
    raw_urls: list[str] = []
    if hero_image.strip():
        raw_urls.append(hero_image)
    raw_urls.extend(match.group(1) for match in MARKDOWN_URL_RE.finditer(markdown_body))
    raw_urls.extend(match.group(2) for match in HTML_MEDIA_URL_RE.finditer(markdown_body))

    references: set[str] = set()
    for raw_url in raw_urls:
        public_url = normalize_public_reference(raw_url)
        if public_url and _looks_like_public_asset_url(public_url, known_urls):
            references.add(public_url)
    return sorted(references)


def normalize_public_reference(raw_url: str) -> str | None:
    cleaned = raw_url.strip().strip('"\'')
    if not cleaned:
        return None
    if cleaned.startswith("<") and cleaned.endswith(">"):
        cleaned = cleaned[1:-1].strip()
    cleaned = cleaned.split()[0].strip().strip('"\'')

    lowered = cleaned.lower()
    if lowered.startswith(("#", "mailto:", "tel:", "data:")):
        return None

    parsed = urlsplit(cleaned)
    if parsed.scheme or parsed.netloc:
        return None

    path = unquote(parsed.path).replace("\\", "/")
    if not path:
        return None
    if not path.startswith("/"):
        if path.startswith(("uploads/", "images/", "files/")) or path in {"favicon.svg", "robots.txt"}:
            path = f"/{path}"
        else:
            return None
    return re.sub(r"/+", "/", path)


def _scan_public_assets(repo_root: Path) -> list[LibraryItem]:
    public_root = repo_root / "public"
    if not public_root.is_dir():
        return []

    items: list[LibraryItem] = []
    for path in sorted(public_root.rglob("*")):
        if path.is_file():
            items.append(_read_asset_library_item(repo_root, path))
    return items


def _read_markdown_library_item(
    repo_root: Path,
    path: Path,
    collection: str,
    known_public_urls: Iterable[str],
) -> LibraryItem:
    collection_root = repo_root / "src" / "content" / collection
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    frontmatter, body = split_frontmatter(text)
    data = parse_frontmatter(frontmatter) if frontmatter else {}
    relative_slug = path.relative_to(collection_root).with_suffix("").as_posix()
    content_type = "blog" if collection == "blog" else "page"
    date_value = str(data.get("pubDate") or "")
    updated_date_value = str(data.get("updatedDate") or "")
    hero_image = str(data.get("heroImage") or "")

    return LibraryItem(
        type=content_type,
        kind="post" if collection == "blog" else "page",
        title=str(data.get("title") or guess_title_from_path(path)),
        slug=relative_slug,
        relative_path=path.relative_to(repo_root).as_posix(),
        public_url=f"/{'blog' if collection == 'blog' else 'pages'}/{relative_slug}/",
        description=str(data.get("description") or ""),
        author=str(data.get("author") or ""),
        date=date_value,
        updated_date=updated_date_value,
        tags=_metadata_list(data.get("tags")),
        draft=_metadata_bool(data.get("draft")),
        featured=_metadata_bool(data.get("featured")),
        order=_metadata_int(data.get("order"), None),
        hero_image=hero_image,
        file_size=_file_size(path),
        modified_time=_modified_time(path),
        references=extract_public_references(body, hero_image, known_public_urls),
    )


def _read_asset_library_item(repo_root: Path, path: Path) -> LibraryItem:
    public_root = repo_root / "public"
    public_url = "/" + path.relative_to(public_root).as_posix()
    return LibraryItem(
        type="asset",
        kind=asset_category(path.suffix.lower()),
        title=path.name,
        slug=path.stem,
        relative_path=path.relative_to(repo_root).as_posix(),
        public_url=public_url,
        file_size=_file_size(path),
        modified_time=_modified_time(path),
    )


def _attach_reverse_references(markdown_items: list[LibraryItem], asset_items: list[LibraryItem]) -> None:
    assets_by_url = {item.public_url: item for item in asset_items if item.public_url}
    for markdown_item in markdown_items:
        markdown_item.references = sorted(set(markdown_item.references))
        for public_url in markdown_item.references:
            asset_item = assets_by_url.get(public_url)
            if asset_item:
                asset_item.referenced_by.append(markdown_item.relative_path)

    for asset_item in asset_items:
        asset_item.referenced_by = sorted(set(asset_item.referenced_by))


def _library_sort_key(item: LibraryItem) -> tuple[int, str]:
    type_order = {"blog": 0, "page": 1, "asset": 2}
    return type_order.get(item.type, 99), item.relative_path.lower()


def _markdown_collection_for_path(repo_root: Path, path: Path) -> str:
    try:
        relative_parts = path.relative_to(repo_root).parts
    except ValueError as exc:
        raise ValueError(f"Path is outside the repository: {path}") from exc

    if len(relative_parts) >= 4 and relative_parts[:3] == ("src", "content", "blog"):
        return "blog"
    if len(relative_parts) >= 4 and relative_parts[:3] == ("src", "content", "pages"):
        return "pages"
    raise ValueError(f"Selected Markdown is not in src/content/blog or src/content/pages: {path}")


def _should_write_frontmatter_value(key: str, value: object) -> bool:
    if value is None:
        return False
    if key in {"heroImage", "updatedDate"} and not str(value).strip():
        return False
    return True


def _frontmatter_value_lines(key: str, value: object) -> list[str]:
    if isinstance(value, bool):
        return [f"{key}: {yaml_bool(value)}"]
    if isinstance(value, int):
        return [f"{key}: {value}"]
    if isinstance(value, float):
        return [f"{key}: {value}"]
    if isinstance(value, list):
        if not value:
            return [f"{key}: []"]
        lines = [f"{key}:"]
        for item in value:
            lines.append(f"  - {_yaml_scalar(item)}")
        return lines
    return [f"{key}: {yaml_string(str(value))}"]


def _yaml_scalar(value: object) -> str:
    if isinstance(value, bool):
        return yaml_bool(value)
    if isinstance(value, int | float):
        return str(value)
    return yaml_string(str(value))


def _looks_like_public_asset_url(public_url: str, known_public_urls: set[str]) -> bool:
    return (
        public_url in known_public_urls
        or public_url.startswith(PUBLIC_REFERENCE_PREFIXES)
        or public_url in PUBLIC_ROOT_REFERENCES
    )


def _metadata_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [piece.strip() for piece in value.split(",") if piece.strip()]
    return []


def _metadata_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _metadata_int(value: object, default: int | None) -> int | None:
    if value is None or value == "":
        return default
    try:
        return int(str(value))
    except ValueError:
        return default


def _file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def _modified_time(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime).replace(microsecond=0).isoformat(sep=" ")
    except OSError:
        return ""


def _parse_scalar(value: str) -> object:
    lower = value.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if value.startswith("[") and value.endswith("]"):
        return _parse_inline_array(value)
    return _strip_quotes(value)


def _parse_inline_array(value: str) -> list[object]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, list):
        return parsed

    inner = value[1:-1].strip()
    if not inner:
        return []
    return [_strip_quotes(item.strip()) for item in inner.split(",") if item.strip()]


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def import_paths(
    repo_root: Path,
    paths: Iterable[str | Path],
    content_type: str,
    metadata: PublishMetadata,
) -> list[ImportResult]:
    repo_root = require_repo_root(repo_root)
    source_paths = [Path(path).expanduser().resolve(strict=False) for path in paths]
    if not source_paths:
        raise ValueError("No files selected.")

    selected_type = content_type.lower().strip()
    if selected_type in {"blog post", "blog", "post"}:
        collection = "blog"
    elif selected_type in {"page", "pages"}:
        collection = "pages"
    elif selected_type in {"asset only", "asset", "assets"}:
        collection = "asset"
    else:
        raise ValueError(f"Unknown content type: {content_type}")

    results: list[ImportResult] = []
    single_file = len(source_paths) == 1
    for source in source_paths:
        if not source.is_file():
            raise ValueError(f"File does not exist: {source}")
        if collection != "asset" and source.suffix.lower() in MARKDOWN_EXTENSIONS:
            desired_slug = metadata.slug if single_file and metadata.slug.strip() else source.stem
            results.append(import_markdown(repo_root, source, collection, metadata, desired_slug))
        else:
            desired_name = metadata.slug if single_file and metadata.slug.strip() else source.name
            results.append(import_asset(repo_root, source, metadata, desired_name))
    return results


def import_markdown(
    repo_root: Path,
    source: Path,
    collection: str,
    metadata: PublishMetadata,
    desired_slug: str,
) -> ImportResult:
    if collection not in {"blog", "pages"}:
        raise ValueError(f"Markdown collection must be blog or pages, got {collection}")
    validate_metadata(collection, metadata)

    text = source.read_text(encoding="utf-8-sig", errors="replace")
    _frontmatter, body = split_frontmatter(text)
    if not body.strip():
        body = "## Notes\n\nWrite your content here."

    destination_dir = repo_root / "src" / "content" / collection
    destination_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(desired_slug)
    destination = unique_path(destination_dir, slug, ".md")
    output = compose_markdown(collection, metadata, body)
    destination.write_text(output, encoding="utf-8", newline="\n")

    public_url = f"/{'blog' if collection == 'blog' else 'pages'}/{destination.stem}/"
    return ImportResult(source, destination, public_url, collection, "Imported Markdown content")


def import_asset(repo_root: Path, source: Path, metadata: PublishMetadata, desired_name: str) -> ImportResult:
    category = asset_category(source.suffix.lower())
    year = year_from_metadata(metadata)
    destination_dir = repo_root / "public" / "uploads" / category / year
    destination_dir.mkdir(parents=True, exist_ok=True)

    clean_name = Path(desired_name).name.strip() or source.name
    desired_path = Path(clean_name)
    suffix = desired_path.suffix or source.suffix
    stem = slugify(desired_path.stem or source.stem, fallback="asset")
    destination = unique_path(destination_dir, stem, suffix.lower())
    shutil.copy2(source, destination)

    public_url = "/" + destination.relative_to(repo_root / "public").as_posix()
    return ImportResult(source, destination, public_url, category, "Imported asset")


def asset_category(suffix: str) -> str:
    if suffix in IMAGE_EXTENSIONS:
        return "images"
    if suffix in AUDIO_EXTENSIONS:
        return "audio"
    if suffix in VIDEO_EXTENSIONS:
        return "video"
    if suffix in DOCUMENT_EXTENSIONS:
        return "files"
    return "files"


def year_from_metadata(metadata: PublishMetadata) -> str:
    match = re.match(r"(\d{4})", metadata.date.strip())
    return match.group(1) if match else str(datetime.now().year)


def unique_path(directory: Path, stem: str, suffix: str) -> Path:
    clean_stem = slugify(stem, fallback="item")
    clean_suffix = suffix if suffix.startswith(".") else f".{suffix}"
    candidate = directory / f"{clean_stem}{clean_suffix}"
    index = 2
    while candidate.exists():
        candidate = directory / f"{clean_stem}-{index}{clean_suffix}"
        index += 1
    return candidate


def compose_markdown(collection: str, metadata: PublishMetadata, body: str) -> str:
    frontmatter = build_frontmatter(collection, metadata)
    return f"{frontmatter}\n\n{body.rstrip()}\n"


def build_frontmatter(collection: str, metadata: PublishMetadata) -> str:
    validate_metadata(collection, metadata)
    lines = ["---"]
    lines.append(f"title: {yaml_string(metadata.title)}")
    lines.append(f"description: {yaml_string(metadata.description)}")

    if collection == "blog":
        lines.append(f"pubDate: {format_datetime(metadata.date, metadata.time)}")
        lines.append(f"author: {yaml_string(metadata.author)}")
        lines.append("tags:")
        for tag in parse_tags(metadata.tags):
            lines.append(f"  - {yaml_string(tag)}")
        if metadata.hero_image.strip():
            lines.append(f"heroImage: {yaml_string(metadata.hero_image.strip())}")
        lines.append(f"draft: {yaml_bool(metadata.draft)}")
        lines.append(f"featured: {yaml_bool(metadata.featured)}")
    elif collection == "pages":
        if metadata.date.strip():
            lines.append(f"updatedDate: {format_datetime(metadata.date, metadata.time)}")
        lines.append(f"order: {int(metadata.order)}")
        lines.append(f"draft: {yaml_bool(metadata.draft)}")
    else:
        raise ValueError(f"Unknown collection: {collection}")

    lines.append("---")
    return "\n".join(lines)


def validate_metadata(collection: str, metadata: PublishMetadata) -> None:
    if not metadata.title.strip():
        raise ValueError("Title is required.")
    description_length = len(metadata.description.strip())
    if description_length < 20 or description_length > 180:
        raise ValueError("Description must be between 20 and 180 characters for the current Astro schema.")
    if collection == "blog":
        if not metadata.author.strip():
            raise ValueError("Author is required for blog posts.")
        if not metadata.date.strip():
            raise ValueError("Publication date is required for blog posts.")
        if not parse_tags(metadata.tags):
            raise ValueError("At least one tag is required for blog posts.")
    if collection == "pages":
        int(metadata.order)


def yaml_string(value: str) -> str:
    return json.dumps(str(value).strip(), ensure_ascii=False)


def yaml_bool(value: bool) -> str:
    return "true" if value else "false"


def format_datetime(date_value: str, time_value: str = "") -> str:
    date_part = date_value.strip() or datetime.now().date().isoformat()
    time_part = time_value.strip()
    if "T" in date_part or not time_part:
        return date_part
    if re.fullmatch(r"\d{2}:\d{2}", time_part):
        time_part = f"{time_part}:00"
    return f"{date_part}T{time_part}"


def run_build(repo_root: Path, log: LogCallback) -> int:
    return run_command(repo_root, ["npm", "run", "build"], log)


def git_status(repo_root: Path, log: LogCallback) -> int:
    return run_command(repo_root, ["git", "status", "--short"], log)


def commit_and_push(repo_root: Path, message: str, log: LogCallback) -> int:
    if not message.strip():
        raise ValueError("Commit message is required.")

    for args in (["git", "add", "."], ["git", "commit", "-m", message.strip()], ["git", "push"]):
        code = run_command(repo_root, list(args), log)
        if code != 0:
            return code
    return 0


def run_command(repo_root: Path, args: list[str], log: LogCallback) -> int:
    repo_root = require_repo_root(repo_root)
    log(f"\n$ {subprocess.list2cmdline(args)}\n")

    command: str | list[str] = args
    use_shell = False
    if os.name == "nt" and args and args[0].lower() == "npm":
        command = subprocess.list2cmdline(args)
        use_shell = True

    try:
        process = subprocess.Popen(
            command,
            cwd=repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=use_shell,
            bufsize=1,
        )
    except OSError as exc:
        log(f"Failed to start command: {exc}\n")
        return 1

    assert process.stdout is not None
    for line in process.stdout:
        log(line)
    code = process.wait()
    if code != 0:
        log(f"Command failed with exit code {code}.\n")
    else:
        log("Command completed successfully.\n")
    return code