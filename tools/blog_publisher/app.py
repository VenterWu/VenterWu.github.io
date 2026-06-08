"""Tkinter GUI for the local blog publisher."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Callable
import webbrowser

from . import publisher


CONTENT_TYPE_TO_COLLECTION = {
    "Blog Post": "blog",
    "Page": "pages",
    "Asset Only": "asset",
}
COLLECTION_TO_CONTENT_TYPE = {value: key for key, value in CONTENT_TYPE_TO_COLLECTION.items()}


class BlogPublisherApp:
    def __init__(self, root: tk.Tk, repo_path: Path | None = None) -> None:
        self.root = root
        self.root.title("Personal Blog Publisher")
        self.root.minsize(980, 720)

        detected_root = publisher.find_repo_root(repo_path or Path.cwd()) or Path.cwd()
        today = datetime.now()

        self.ui_queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self.file_paths: list[Path] = []

        self.repo_var = tk.StringVar(value=str(detected_root))
        self.content_type_var = tk.StringVar(value="Blog Post")
        self.collection_var = tk.StringVar(value="blog")
        self.title_var = tk.StringVar()
        self.slug_var = tk.StringVar()
        self.description_var = tk.StringVar()
        self.author_var = tk.StringVar(value=publisher.read_default_author(detected_root) if detected_root.exists() else publisher.DEFAULT_AUTHOR)
        self.date_var = tk.StringVar(value=today.date().isoformat())
        self.time_var = tk.StringVar(value=today.strftime("%H:%M"))
        self.tags_var = tk.StringVar(value=publisher.DEFAULT_TAG)
        self.hero_image_var = tk.StringVar()
        self.order_var = tk.StringVar(value="100")
        self.draft_var = tk.BooleanVar(value=False)
        self.featured_var = tk.BooleanVar(value=False)

        self._build_ui()
        self._poll_ui_queue()

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main = ttk.Frame(self.root, padding=12)
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(2, weight=1)
        main.rowconfigure(4, weight=1)

        self._build_repo_frame(main)
        self._build_import_frame(main)
        self._build_publish_frame(main)
        self._build_output_frame(main)

    def _build_repo_frame(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Repository", padding=8)
        frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Root").grid(row=0, column=0, sticky="w", padx=(0, 6))
        ttk.Entry(frame, textvariable=self.repo_var).grid(row=0, column=1, sticky="ew", padx=(0, 6))
        ttk.Button(frame, text="Browse", command=self._browse_repo).grid(row=0, column=2, padx=(0, 6))
        ttk.Button(frame, text="Detect", command=self._detect_repo).grid(row=0, column=3)

    def _build_import_frame(self, parent: ttk.Frame) -> None:
        frame = ttk.Frame(parent)
        frame.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        files_frame = ttk.LabelFrame(frame, text="Files", padding=8)
        files_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        files_frame.columnconfigure(0, weight=1)
        files_frame.rowconfigure(0, weight=1)

        self.files_listbox = tk.Listbox(files_frame, selectmode=tk.EXTENDED, height=10)
        self.files_listbox.grid(row=0, column=0, columnspan=4, sticky="nsew", pady=(0, 8))
        ttk.Button(files_frame, text="Add Files", command=self._add_files).grid(row=1, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(files_frame, text="Remove", command=self._remove_selected_files).grid(row=1, column=1, sticky="ew", padx=(0, 6))
        ttk.Button(files_frame, text="Clear", command=self._clear_files).grid(row=1, column=2, sticky="ew", padx=(0, 6))
        ttk.Button(files_frame, text="Import Selected", command=self._import_selected).grid(row=1, column=3, sticky="ew")

        metadata_frame = ttk.LabelFrame(frame, text="Metadata", padding=8)
        metadata_frame.grid(row=0, column=1, sticky="nsew")
        metadata_frame.columnconfigure(1, weight=1)
        metadata_frame.columnconfigure(3, weight=1)

        self._add_label(metadata_frame, "Content type", 0, 0)
        type_box = ttk.Combobox(
            metadata_frame,
            textvariable=self.content_type_var,
            values=list(CONTENT_TYPE_TO_COLLECTION),
            state="readonly",
        )
        type_box.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=3)
        type_box.bind("<<ComboboxSelected>>", self._sync_collection_from_content_type)

        self._add_label(metadata_frame, "Collection/type", 0, 2)
        collection_box = ttk.Combobox(
            metadata_frame,
            textvariable=self.collection_var,
            values=["blog", "pages", "asset"],
            state="readonly",
        )
        collection_box.grid(row=0, column=3, sticky="ew", pady=3)
        collection_box.bind("<<ComboboxSelected>>", self._sync_content_type_from_collection)

        rows = [
            ("Title", self.title_var),
            ("Slug / destination", self.slug_var),
            ("Description", self.description_var),
            ("Author", self.author_var),
            ("Date", self.date_var),
            ("Time", self.time_var),
            ("Tags", self.tags_var),
            ("Hero image", self.hero_image_var),
            ("Page order", self.order_var),
        ]
        for index, (label, variable) in enumerate(rows, start=1):
            self._add_label(metadata_frame, label, index, 0)
            column_span = 3 if label in {"Title", "Slug / destination", "Description", "Hero image"} else 1
            entry = ttk.Entry(metadata_frame, textvariable=variable)
            entry.grid(row=index, column=1, columnspan=column_span, sticky="ew", padx=(0, 8), pady=3)

        ttk.Checkbutton(metadata_frame, text="Draft", variable=self.draft_var).grid(row=10, column=1, sticky="w", pady=(6, 0))
        ttk.Checkbutton(metadata_frame, text="Featured", variable=self.featured_var).grid(row=10, column=2, sticky="w", pady=(6, 0))

    def _build_publish_frame(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Publish", padding=8)
        frame.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        for column in range(5):
            frame.columnconfigure(column, weight=1)

        ttk.Button(frame, text="Run Build", command=self._run_build).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(frame, text="Git Status", command=self._git_status).grid(row=0, column=1, sticky="ew", padx=(0, 6))
        ttk.Button(frame, text="Commit & Push", command=self._commit_and_push).grid(row=0, column=2, sticky="ew", padx=(0, 6))
        ttk.Button(frame, text="Open Site", command=self._open_site).grid(row=0, column=3, sticky="ew", padx=(0, 6))
        ttk.Button(frame, text="Open Repo", command=self._open_repo).grid(row=0, column=4, sticky="ew")

    def _build_output_frame(self, parent: ttk.Frame) -> None:
        frame = ttk.Frame(parent)
        frame.grid(row=4, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        ttk.Label(frame, text="Public URLs").grid(row=0, column=0, sticky="w")
        self.urls_text = tk.Text(frame, height=4, wrap="none")
        self.urls_text.grid(row=1, column=0, sticky="ew", pady=(2, 8))

        ttk.Label(frame, text="Log").grid(row=2, column=0, sticky="w")
        self.log_text = tk.Text(frame, height=12, wrap="word")
        self.log_text.grid(row=3, column=0, sticky="nsew", pady=(2, 0))

    def _add_label(self, parent: ttk.Frame, text: str, row: int, column: int) -> None:
        ttk.Label(parent, text=text).grid(row=row, column=column, sticky="w", padx=(0, 6), pady=3)

    def _browse_repo(self) -> None:
        path = filedialog.askdirectory(title="Select Astro repository root")
        if path:
            self.repo_var.set(path)
            self._refresh_author_default()

    def _detect_repo(self) -> None:
        root = publisher.find_repo_root(self.repo_var.get()) or publisher.find_repo_root(Path.cwd())
        if root:
            self.repo_var.set(str(root))
            self._refresh_author_default()
            self._log(f"Detected repository: {root}\n")
        else:
            messagebox.showwarning("Repository not found", "Could not find package.json and astro.config.ts above the selected path.")

    def _refresh_author_default(self) -> None:
        try:
            repo_root = publisher.require_repo_root(self.repo_var.get())
        except ValueError:
            return
        if not self.author_var.get().strip() or self.author_var.get().strip() == publisher.DEFAULT_AUTHOR:
            self.author_var.set(publisher.read_default_author(repo_root))

    def _add_files(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Select content or asset files",
            filetypes=[
                ("Supported files", "*.md *.mdx *.pdf *.jpg *.jpeg *.png *.gif *.webp *.svg *.mp4 *.webm *.mov *.mp3 *.wav *.m4a *.ogg *.*"),
                ("Markdown", "*.md *.mdx"),
                ("Images", "*.jpg *.jpeg *.png *.gif *.webp *.svg"),
                ("Documents", "*.pdf *.doc *.docx *.ppt *.pptx *.xls *.xlsx *.txt *.zip"),
                ("Video", "*.mp4 *.webm *.mov"),
                ("Audio", "*.mp3 *.wav *.m4a *.ogg"),
                ("All files", "*.*"),
            ],
        )
        if not paths:
            return

        existing = {path.resolve(strict=False) for path in self.file_paths}
        for raw_path in paths:
            path = Path(raw_path).resolve(strict=False)
            if path not in existing:
                self.file_paths.append(path)
                existing.add(path)
                self.files_listbox.insert(tk.END, str(path))
        self._populate_metadata_from_file(self.file_paths[0])

    def _remove_selected_files(self) -> None:
        selected = sorted(self.files_listbox.curselection(), reverse=True)
        for index in selected:
            self.files_listbox.delete(index)
            del self.file_paths[index]
        if self.file_paths:
            self._populate_metadata_from_file(self.file_paths[0])

    def _clear_files(self) -> None:
        self.file_paths.clear()
        self.files_listbox.delete(0, tk.END)

    def _populate_metadata_from_file(self, path: Path) -> None:
        self.slug_var.set(publisher.slugify(path.stem) if path.suffix.lower() in publisher.MARKDOWN_EXTENSIONS else path.name)
        self.title_var.set(publisher.guess_title_from_path(path))

        if path.suffix.lower() not in publisher.MARKDOWN_EXTENSIONS:
            return

        data = publisher.read_markdown_metadata(path)
        self.title_var.set(str(data.get("title") or publisher.guess_title_from_path(path)))
        self.description_var.set(str(data.get("description") or self.description_var.get()))
        self.author_var.set(str(data.get("author") or self.author_var.get() or publisher.DEFAULT_AUTHOR))
        self.hero_image_var.set(str(data.get("heroImage") or self.hero_image_var.get()))
        self.draft_var.set(bool(data.get("draft", self.draft_var.get())))
        self.featured_var.set(bool(data.get("featured", self.featured_var.get())))
        if "order" in data:
            self.order_var.set(str(data["order"]))
        if isinstance(data.get("tags"), list):
            self.tags_var.set(", ".join(str(tag) for tag in data["tags"]))
        elif data.get("tags"):
            self.tags_var.set(str(data["tags"]))

        date_value = str(data.get("pubDate") or data.get("updatedDate") or "")
        if date_value:
            date_part, time_part = self._split_datetime(date_value)
            self.date_var.set(date_part)
            if time_part:
                self.time_var.set(time_part)

    def _split_datetime(self, value: str) -> tuple[str, str]:
        value = value.strip().replace("Z", "")
        if "T" in value:
            date_part, time_part = value.split("T", 1)
            return date_part[:10], time_part[:5]
        if " " in value:
            date_part, time_part = value.split(" ", 1)
            return date_part[:10], time_part[:5]
        return value[:10], ""

    def _sync_collection_from_content_type(self, _event: object | None = None) -> None:
        self.collection_var.set(CONTENT_TYPE_TO_COLLECTION.get(self.content_type_var.get(), "blog"))

    def _sync_content_type_from_collection(self, _event: object | None = None) -> None:
        self.content_type_var.set(COLLECTION_TO_CONTENT_TYPE.get(self.collection_var.get(), "Blog Post"))

    def _metadata_from_form(self) -> publisher.PublishMetadata:
        try:
            order = int(self.order_var.get().strip() or "100")
        except ValueError as exc:
            raise ValueError("Page order must be a number.") from exc
        return publisher.PublishMetadata(
            title=self.title_var.get(),
            slug=self.slug_var.get(),
            description=self.description_var.get(),
            author=self.author_var.get(),
            date=self.date_var.get(),
            time=self.time_var.get(),
            tags=publisher.parse_tags(self.tags_var.get()),
            draft=self.draft_var.get(),
            featured=self.featured_var.get(),
            order=order,
            hero_image=self.hero_image_var.get(),
        )

    def _repo_root(self) -> Path:
        return publisher.require_repo_root(self.repo_var.get())

    def _selected_content_type(self) -> str:
        collection = self.collection_var.get()
        if collection == "blog":
            return "Blog Post"
        if collection == "pages":
            return "Page"
        return "Asset Only"

    def _import_selected(self) -> None:
        try:
            repo_root = self._repo_root()
            metadata = self._metadata_from_form()
        except ValueError as exc:
            messagebox.showerror("Cannot import", str(exc))
            return
        selected_paths = list(self.file_paths)
        content_type = self._selected_content_type()

        def task() -> None:
            results = publisher.import_paths(repo_root, selected_paths, content_type, metadata)
            for result in results:
                self._log(f"{result.message}: {result.source} -> {result.destination}\n")
                self._add_url(result.public_url)
            self._log("Import completed. Run Build before committing.\n")

        self._run_worker("Import Selected", task)

    def _run_build(self) -> None:
        try:
            repo_root = self._repo_root()
        except ValueError as exc:
            messagebox.showerror("Cannot build", str(exc))
            return
        self._run_worker("Run Build", lambda: publisher.run_build(repo_root, self._log))

    def _git_status(self) -> None:
        try:
            repo_root = self._repo_root()
        except ValueError as exc:
            messagebox.showerror("Cannot run git status", str(exc))
            return
        self._run_worker("Git Status", lambda: publisher.git_status(repo_root, self._log))

    def _commit_and_push(self) -> None:
        try:
            repo_root = self._repo_root()
        except ValueError as exc:
            messagebox.showerror("Cannot commit", str(exc))
            return
        message = simpledialog.askstring("Commit message", "Enter a commit message:", parent=self.root)
        if not message:
            self._log("Commit cancelled.\n")
            return
        self._run_worker("Commit & Push", lambda: publisher.commit_and_push(repo_root, message, self._log))

    def _open_site(self) -> None:
        try:
            url = publisher.read_site_url(self._repo_root())
        except ValueError:
            url = publisher.SITE_URL_FALLBACK
        webbrowser.open(url)
        self._log(f"Opened site: {url}\n")

    def _open_repo(self) -> None:
        try:
            url = publisher.read_repo_url(self._repo_root())
        except ValueError:
            url = publisher.REPO_URL_FALLBACK
        webbrowser.open(url)
        self._log(f"Opened repo: {url}\n")

    def _run_worker(self, title: str, callback: Callable[[], object]) -> None:
        def worker() -> None:
            self._log(f"\n== {title} ==\n")
            try:
                callback()
            except Exception as exc:
                self._log(f"ERROR: {exc}\n")

        threading.Thread(target=worker, daemon=True).start()

    def _log(self, text: str) -> None:
        self.ui_queue.put(("log", text))

    def _add_url(self, url: str) -> None:
        self.ui_queue.put(("url", url))

    def _poll_ui_queue(self) -> None:
        while True:
            try:
                kind, text = self.ui_queue.get_nowait()
            except queue.Empty:
                break
            if kind == "url":
                self.urls_text.insert(tk.END, text + "\n")
                self.urls_text.see(tk.END)
            else:
                self.log_text.insert(tk.END, text)
                self.log_text.see(tk.END)
        self.root.after(100, self._poll_ui_queue)


def run_app(repo_path: Path | None = None) -> None:
    root = tk.Tk()
    BlogPublisherApp(root, repo_path)
    root.mainloop()