"""Tkinter GUI for the local blog publisher."""

from __future__ import annotations

from datetime import datetime
import os
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
        self.root.minsize(1180, 780)

        detected_root = publisher.find_repo_root(repo_path or Path.cwd()) or Path.cwd()
        today = datetime.now()

        self.ui_queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self.file_paths: list[Path] = []
        self.library_items: list[publisher.LibraryItem] = []
        self.library_items_by_path: dict[str, publisher.LibraryItem] = {}
        self.tree_path_by_id: dict[str, Path] = {}
        self.selected_library_item: publisher.LibraryItem | None = None
        self.selected_path: Path | None = None
        self.selected_public_url = ""

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

        self.library_filter_var = tk.StringVar(value="All")
        self.library_search_var = tk.StringVar()
        self.existing_title_var = tk.StringVar()
        self.existing_description_var = tk.StringVar()
        self.existing_author_var = tk.StringVar()
        self.existing_date_var = tk.StringVar()
        self.existing_time_var = tk.StringVar()
        self.existing_tags_var = tk.StringVar()
        self.existing_hero_image_var = tk.StringVar()
        self.existing_order_var = tk.StringVar(value="100")
        self.existing_draft_var = tk.BooleanVar(value=False)
        self.existing_featured_var = tk.BooleanVar(value=False)

        self._build_ui()
        self._refresh_library(show_log=False)
        self._poll_ui_queue()

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main = ttk.Frame(self.root, padding=12)
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=3)
        main.rowconfigure(3, weight=2)

        self._build_repo_frame(main)
        workspace = ttk.PanedWindow(main, orient=tk.HORIZONTAL)
        workspace.grid(row=1, column=0, sticky="nsew", pady=(0, 8))

        tree_frame = self._build_repository_tree_frame(workspace)
        workspace.add(tree_frame, weight=1)

        notebook = ttk.Notebook(workspace)
        import_tab = ttk.Frame(notebook, padding=8)
        library_tab = ttk.Frame(notebook, padding=8)
        import_tab.columnconfigure(0, weight=1)
        import_tab.rowconfigure(0, weight=1)
        library_tab.columnconfigure(0, weight=1)
        library_tab.rowconfigure(1, weight=1)
        notebook.add(import_tab, text="Import")
        notebook.add(library_tab, text="Library")
        workspace.add(notebook, weight=4)

        self._build_import_frame(import_tab)
        self._build_library_frame(library_tab)
        self._build_publish_frame(main)
        self._build_output_frame(main)

    def _build_repository_tree_frame(self, parent: ttk.PanedWindow) -> ttk.Frame:
        frame = ttk.LabelFrame(parent, text="Repository Tree", padding=8)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        ttk.Button(frame, text="Refresh Library", command=self._refresh_library).grid(row=0, column=0, sticky="ew", pady=(0, 6))

        tree_container = ttk.Frame(frame)
        tree_container.grid(row=1, column=0, sticky="nsew")
        tree_container.columnconfigure(0, weight=1)
        tree_container.rowconfigure(0, weight=1)

        self.repository_tree = ttk.Treeview(tree_container, show="tree", selectmode="browse")
        tree_scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.repository_tree.yview)
        self.repository_tree.configure(yscrollcommand=tree_scrollbar.set)
        self.repository_tree.grid(row=0, column=0, sticky="nsew")
        tree_scrollbar.grid(row=0, column=1, sticky="ns")
        self.repository_tree.bind("<<TreeviewSelect>>", self._on_repository_tree_select)
        return frame

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
        frame.grid(row=0, column=0, sticky="nsew")
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

    def _build_library_frame(self, parent: ttk.Frame) -> None:
        controls = ttk.Frame(parent)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        controls.columnconfigure(3, weight=1)

        ttk.Button(controls, text="Refresh Library", command=self._refresh_library).grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Label(controls, text="Filter").grid(row=0, column=1, sticky="w", padx=(0, 4))
        filter_box = ttk.Combobox(
            controls,
            textvariable=self.library_filter_var,
            values=["All", "Blog", "Pages", "Assets"],
            state="readonly",
            width=10,
        )
        filter_box.grid(row=0, column=2, sticky="w", padx=(0, 12))
        filter_box.bind("<<ComboboxSelected>>", lambda _event: self._apply_library_filters())

        ttk.Label(controls, text="Search").grid(row=0, column=3, sticky="e", padx=(0, 4))
        search_entry = ttk.Entry(controls, textvariable=self.library_search_var)
        search_entry.grid(row=0, column=4, sticky="ew")
        controls.columnconfigure(4, weight=1)
        self.library_search_var.trace_add("write", lambda *_args: self._apply_library_filters())

        content = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        content.grid(row=1, column=0, sticky="nsew")

        table_frame = ttk.Frame(content)
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        columns = ("type", "title", "date", "tags", "draft", "path")
        self.library_table = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        headings = {
            "type": "Type",
            "title": "Title / Name",
            "date": "Date",
            "tags": "Tags / Kind",
            "draft": "Draft",
            "path": "Path",
        }
        widths = {"type": 70, "title": 180, "date": 120, "tags": 150, "draft": 60, "path": 280}
        for column in columns:
            self.library_table.heading(column, text=headings[column])
            self.library_table.column(column, width=widths[column], anchor="w", stretch=column in {"title", "path"})
        table_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.library_table.yview)
        self.library_table.configure(yscrollcommand=table_scrollbar.set)
        self.library_table.grid(row=0, column=0, sticky="nsew")
        table_scrollbar.grid(row=0, column=1, sticky="ns")
        self.library_table.bind("<<TreeviewSelect>>", self._on_library_select)
        content.add(table_frame, weight=3)

        details_frame = ttk.Frame(content)
        details_frame.columnconfigure(0, weight=1)
        details_frame.rowconfigure(2, weight=1)
        content.add(details_frame, weight=2)

        actions = ttk.Frame(details_frame)
        actions.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        for column in range(4):
            actions.columnconfigure(column, weight=1)
        ttk.Button(actions, text="Open File", command=self._open_selected_file).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(actions, text="Open Folder", command=self._open_selected_folder).grid(row=0, column=1, sticky="ew", padx=(0, 4))
        ttk.Button(actions, text="Copy Public URL", command=self._copy_selected_public_url).grid(row=0, column=2, sticky="ew", padx=(0, 4))
        self.save_metadata_button = ttk.Button(actions, text="Save Metadata", command=self._save_existing_metadata, state=tk.DISABLED)
        self.save_metadata_button.grid(row=0, column=3, sticky="ew")

        ttk.Label(details_frame, text="Properties and Relations").grid(row=1, column=0, sticky="w")
        self.properties_text = tk.Text(details_frame, height=10, wrap="word", state=tk.DISABLED)
        self.properties_text.grid(row=2, column=0, sticky="nsew", pady=(2, 8))

        metadata_frame = ttk.LabelFrame(details_frame, text="Existing Item Metadata", padding=8)
        metadata_frame.grid(row=3, column=0, sticky="ew")
        metadata_frame.columnconfigure(1, weight=1)
        metadata_frame.columnconfigure(3, weight=1)

        rows = [
            ("Title", self.existing_title_var),
            ("Description", self.existing_description_var),
            ("Author", self.existing_author_var),
            ("Date", self.existing_date_var),
            ("Time", self.existing_time_var),
            ("Tags", self.existing_tags_var),
            ("Hero image", self.existing_hero_image_var),
            ("Page order", self.existing_order_var),
        ]
        for index, (label, variable) in enumerate(rows):
            row = index // 2
            label_column = 0 if index % 2 == 0 else 2
            entry_column = 1 if index % 2 == 0 else 3
            self._add_label(metadata_frame, label, row, label_column)
            ttk.Entry(metadata_frame, textvariable=variable).grid(row=row, column=entry_column, sticky="ew", padx=(0, 8), pady=3)

        ttk.Checkbutton(metadata_frame, text="Draft", variable=self.existing_draft_var).grid(row=4, column=1, sticky="w", pady=(6, 0))
        ttk.Checkbutton(metadata_frame, text="Featured", variable=self.existing_featured_var).grid(row=4, column=3, sticky="w", pady=(6, 0))

    def _build_publish_frame(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Publish", padding=8)
        frame.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        for column in range(5):
            frame.columnconfigure(column, weight=1)

        ttk.Button(frame, text="Run Build", command=self._run_build).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(frame, text="Git Status", command=self._git_status).grid(row=0, column=1, sticky="ew", padx=(0, 6))
        ttk.Button(frame, text="Commit & Push", command=self._commit_and_push).grid(row=0, column=2, sticky="ew", padx=(0, 6))
        ttk.Button(frame, text="Open Site", command=self._open_site).grid(row=0, column=3, sticky="ew", padx=(0, 6))
        ttk.Button(frame, text="Open Repo", command=self._open_repo).grid(row=0, column=4, sticky="ew")

    def _build_output_frame(self, parent: ttk.Frame) -> None:
        frame = ttk.Frame(parent)
        frame.grid(row=3, column=0, sticky="nsew")
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

    def _refresh_library(self, show_log: bool = True) -> None:
        try:
            repo_root = self._repo_root()
            items = publisher.scan_content_library(repo_root)
        except Exception as exc:
            if show_log:
                messagebox.showerror("Cannot refresh library", str(exc))
                self._log(f"ERROR: Cannot refresh library: {exc}\n")
            return

        self.library_items = items
        self.library_items_by_path = {item.relative_path: item for item in items}
        self._apply_library_filters()
        self._refresh_repository_tree(repo_root)
        if show_log:
            self._log(f"Refreshed library: {len(items)} items.\n")

    def _apply_library_filters(self) -> None:
        if not hasattr(self, "library_table"):
            return
        for row_id in self.library_table.get_children():
            self.library_table.delete(row_id)

        selected_filter = self.library_filter_var.get()
        query = self.library_search_var.get().strip().lower()

        for item in self.library_items:
            if selected_filter == "Blog" and item.type != "blog":
                continue
            if selected_filter == "Pages" and item.type != "page":
                continue
            if selected_filter == "Assets" and item.type != "asset":
                continue
            if query and query not in self._library_search_text(item):
                continue

            tags_or_kind = ", ".join(item.tags) if item.tags else item.kind
            self.library_table.insert(
                "",
                tk.END,
                iid=item.relative_path,
                values=(
                    item.type,
                    item.title,
                    self._display_date(item),
                    tags_or_kind,
                    "Yes" if item.draft else "",
                    item.relative_path,
                ),
            )

    def _library_search_text(self, item: publisher.LibraryItem) -> str:
        parts = [
            item.type,
            item.kind,
            item.title,
            item.slug,
            item.relative_path,
            item.public_url,
            item.description,
            item.author,
            " ".join(item.tags),
        ]
        return " ".join(parts).lower()

    def _display_date(self, item: publisher.LibraryItem) -> str:
        return item.date or item.updated_date or ""

    def _refresh_repository_tree(self, repo_root: Path) -> None:
        if not hasattr(self, "repository_tree"):
            return
        for node_id in self.repository_tree.get_children():
            self.repository_tree.delete(node_id)
        self.tree_path_by_id.clear()

        for path in (repo_root / "src" / "content", repo_root / "public"):
            if path.exists():
                self._insert_repository_tree_path("", path, repo_root, depth=0)

    def _insert_repository_tree_path(self, parent_id: str, path: Path, repo_root: Path, depth: int) -> None:
        text = path.name
        if path == repo_root / "src" / "content":
            text = "src/content"
        elif path == repo_root / "public":
            text = "public"

        node_id = self.repository_tree.insert(parent_id, tk.END, text=text, open=depth < 1)
        self.tree_path_by_id[node_id] = path
        if not path.is_dir():
            return

        try:
            children = sorted(path.iterdir(), key=lambda child: (child.is_file(), child.name.lower()))
        except OSError:
            return
        for child in children:
            self._insert_repository_tree_path(node_id, child, repo_root, depth + 1)

    def _on_library_select(self, _event: object | None = None) -> None:
        selection = self.library_table.selection()
        if not selection:
            return
        item = self.library_items_by_path.get(selection[0])
        if not item:
            return
        self._select_library_item(item)

    def _on_repository_tree_select(self, _event: object | None = None) -> None:
        selection = self.repository_tree.selection()
        if not selection:
            return
        path = self.tree_path_by_id.get(selection[0])
        if not path:
            return

        try:
            repo_root = self._repo_root()
        except ValueError as exc:
            messagebox.showerror("Repository not found", str(exc))
            return

        try:
            relative_path = path.relative_to(repo_root).as_posix()
        except ValueError:
            relative_path = ""

        item = self.library_items_by_path.get(relative_path)
        if item:
            self._select_library_item(item)
            return

        self.selected_library_item = None
        self.selected_path = path
        self.selected_public_url = self._public_url_for_path(repo_root, path)
        self._clear_existing_metadata()
        self.save_metadata_button.configure(state=tk.DISABLED)
        self._set_properties_for_path(repo_root, path)

    def _select_library_item(self, item: publisher.LibraryItem) -> None:
        try:
            repo_root = self._repo_root()
        except ValueError as exc:
            messagebox.showerror("Repository not found", str(exc))
            return
        self.selected_library_item = item
        self.selected_path = repo_root / item.relative_path
        self.selected_public_url = item.public_url
        self._populate_existing_metadata(item)
        self._set_properties_from_item(item)
        state = tk.NORMAL if item.type in {"blog", "page"} else tk.DISABLED
        self.save_metadata_button.configure(state=state)

    def _populate_existing_metadata(self, item: publisher.LibraryItem) -> None:
        self.existing_title_var.set(item.title)
        self.existing_description_var.set(item.description)
        self.existing_author_var.set(item.author)
        date_part, time_part = self._split_datetime(item.date or item.updated_date)
        self.existing_date_var.set(date_part)
        self.existing_time_var.set(time_part)
        self.existing_tags_var.set(", ".join(item.tags))
        self.existing_hero_image_var.set(item.hero_image)
        self.existing_order_var.set(str(item.order if item.order is not None else 100))
        self.existing_draft_var.set(item.draft)
        self.existing_featured_var.set(item.featured)

    def _clear_existing_metadata(self) -> None:
        for variable in (
            self.existing_title_var,
            self.existing_description_var,
            self.existing_author_var,
            self.existing_date_var,
            self.existing_time_var,
            self.existing_tags_var,
            self.existing_hero_image_var,
        ):
            variable.set("")
        self.existing_order_var.set("100")
        self.existing_draft_var.set(False)
        self.existing_featured_var.set(False)

    def _set_properties_from_item(self, item: publisher.LibraryItem) -> None:
        lines = [
            f"Type: {item.type}",
            f"Kind: {item.kind}",
            f"Title / name: {item.title}",
            f"Slug: {item.slug}",
            f"Path: {item.relative_path}",
            f"Public URL: {item.public_url or '(none)'}",
            f"File size: {self._format_size(item.file_size)}",
            f"Modified: {item.modified_time or '(unknown)'}",
        ]
        if item.description:
            lines.append(f"Description: {item.description}")
        if item.author:
            lines.append(f"Author: {item.author}")
        if item.date:
            lines.append(f"Date: {item.date}")
        if item.updated_date:
            lines.append(f"Updated date: {item.updated_date}")
        if item.tags:
            lines.append(f"Tags: {', '.join(item.tags)}")
        if item.hero_image:
            lines.append(f"Hero image: {item.hero_image}")
        if item.type in {"blog", "page"}:
            lines.append(f"Draft: {item.draft}")
        if item.type == "blog":
            lines.append(f"Featured: {item.featured}")
        if item.order is not None:
            lines.append(f"Order: {item.order}")

        lines.append("")
        lines.append("References:")
        if item.references:
            lines.extend(f"  {public_url}" for public_url in item.references)
        else:
            lines.append("  (none)")
        lines.append("Referenced by:")
        if item.referenced_by:
            lines.extend(f"  {relative_path}" for relative_path in item.referenced_by)
        else:
            lines.append("  (none)")
        self._set_properties_text("\n".join(lines))

    def _set_properties_for_path(self, repo_root: Path, path: Path) -> None:
        relative_path = self._relative_path_for_display(repo_root, path)
        public_url = self._public_url_for_path(repo_root, path)
        lines = [
            f"Type: {'Directory' if path.is_dir() else 'File'}",
            f"Path: {relative_path}",
            f"Public URL: {public_url or '(none)'}",
        ]
        if path.is_file():
            try:
                lines.append(f"File size: {self._format_size(path.stat().st_size)}")
            except OSError:
                lines.append("File size: (unknown)")
        try:
            modified_time = datetime.fromtimestamp(path.stat().st_mtime).replace(microsecond=0).isoformat(sep=" ")
            lines.append(f"Modified: {modified_time}")
        except OSError:
            lines.append("Modified: (unknown)")
        self._set_properties_text("\n".join(lines))

    def _set_properties_text(self, text: str) -> None:
        self.properties_text.configure(state=tk.NORMAL)
        self.properties_text.delete("1.0", tk.END)
        self.properties_text.insert(tk.END, text)
        self.properties_text.configure(state=tk.DISABLED)

    def _existing_metadata_from_form(self) -> publisher.PublishMetadata:
        try:
            order = int(self.existing_order_var.get().strip() or "100")
        except ValueError as exc:
            raise ValueError("Page order must be a number.") from exc
        return publisher.PublishMetadata(
            title=self.existing_title_var.get(),
            slug="",
            description=self.existing_description_var.get(),
            author=self.existing_author_var.get(),
            date=self.existing_date_var.get(),
            time=self.existing_time_var.get(),
            tags=publisher.parse_tags(self.existing_tags_var.get()),
            draft=self.existing_draft_var.get(),
            featured=self.existing_featured_var.get(),
            order=order,
            hero_image=self.existing_hero_image_var.get(),
        )

    def _save_existing_metadata(self) -> None:
        item = self.selected_library_item
        if not item:
            messagebox.showwarning("No item selected", "Select a blog post or page first.")
            return
        if item.type not in {"blog", "page"}:
            messagebox.showinfo("Metadata not editable", "Assets are read-only in this tool.")
            return

        try:
            repo_root = self._repo_root()
            metadata = self._existing_metadata_from_form()
            saved_path = publisher.save_markdown_metadata(repo_root, item.relative_path, metadata)
        except Exception as exc:
            messagebox.showerror("Cannot save metadata", str(exc))
            self._log(f"ERROR: Cannot save metadata: {exc}\n")
            return

        self._log(f"Saved metadata: {saved_path}\n")
        previous_path = item.relative_path
        self._refresh_library(show_log=False)
        if previous_path in self.library_table.get_children():
            self.library_table.selection_set(previous_path)
            self.library_table.focus(previous_path)
            refreshed_item = self.library_items_by_path.get(previous_path)
            if refreshed_item:
                self._select_library_item(refreshed_item)

    def _open_selected_file(self) -> None:
        if not self.selected_path:
            messagebox.showwarning("No file selected", "Select an item in the library or repository tree first.")
            return
        self._open_path(self.selected_path)

    def _open_selected_folder(self) -> None:
        if not self.selected_path:
            messagebox.showwarning("No folder selected", "Select an item in the library or repository tree first.")
            return
        folder = self.selected_path if self.selected_path.is_dir() else self.selected_path.parent
        self._open_path(folder)

    def _copy_selected_public_url(self) -> None:
        if not self.selected_public_url:
            messagebox.showinfo("No public URL", "The selected item does not have a public URL.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(self.selected_public_url)
        self._add_url(self.selected_public_url)
        self._log(f"Copied public URL: {self.selected_public_url}\n")

    def _open_path(self, path: Path) -> None:
        try:
            if hasattr(os, "startfile"):
                os.startfile(str(path))
            else:
                webbrowser.open(path.resolve().as_uri())
        except Exception as exc:
            messagebox.showerror("Cannot open path", str(exc))
            self._log(f"ERROR: Cannot open path: {exc}\n")

    def _public_url_for_path(self, repo_root: Path, path: Path) -> str:
        if not path.is_file():
            return ""
        try:
            return "/" + path.relative_to(repo_root / "public").as_posix()
        except ValueError:
            return ""

    def _relative_path_for_display(self, repo_root: Path, path: Path) -> str:
        try:
            return path.relative_to(repo_root).as_posix()
        except ValueError:
            return str(path)

    def _format_size(self, size: int) -> str:
        if size < 1024:
            return f"{size} B"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size / (1024 * 1024):.1f} MB"

    def _browse_repo(self) -> None:
        path = filedialog.askdirectory(title="Select Astro repository root")
        if path:
            self.repo_var.set(path)
            self._refresh_author_default()
            self._refresh_library()

    def _detect_repo(self) -> None:
        root = publisher.find_repo_root(self.repo_var.get()) or publisher.find_repo_root(Path.cwd())
        if root:
            self.repo_var.set(str(root))
            self._refresh_author_default()
            self._refresh_library()
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
            self.ui_queue.put(("refresh_library", ""))

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
            elif kind == "refresh_library":
                self._refresh_library(show_log=False)
            else:
                self.log_text.insert(tk.END, text)
                self.log_text.see(tk.END)
        self.root.after(100, self._poll_ui_queue)


def run_app(repo_path: Path | None = None) -> None:
    root = tk.Tk()
    BlogPublisherApp(root, repo_path)
    root.mainloop()