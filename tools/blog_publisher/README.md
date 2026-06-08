# Blog Publisher Tool

This folder contains a local Tkinter GUI for importing Markdown and public assets into the Astro blog, browsing and maintaining existing content, then running the build and Git publish commands.

Use one of the repository-root launchers. They change into the repository root before running the Python module, so Python can import `tools.blog_publisher` correctly.

Double-click or run the Windows launcher:

```cmd
Start-BlogPublisher.cmd
```

Run the PowerShell launcher:

```powershell
.\Start-BlogPublisher.ps1
```

If PowerShell execution policy blocks the script, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\Start-BlogPublisher.ps1
```

Or start it manually after changing to the repository root:

```powershell
Set-Location "F:\Project\ProjectForFun\Software\Personal Blog Web"
conda run -n psblog python -m tools.blog_publisher
```

Show command-line help without opening the GUI:

```powershell
.\Start-BlogPublisher.ps1 --help
```

Running `conda run -n psblog python -m tools.blog_publisher --repo "F:\Project\ProjectForFun\Software\Personal Blog Web"` from another directory is not enough unless `PYTHONPATH` already includes the repository root. Python must import `tools.blog_publisher` before the `--repo` argument is parsed.

The GUI supports:

- browsing existing blog posts, pages, and public assets in a `Library` tab;
- viewing a repository tree for `src/content` and `public`, including `public/uploads/` assets;
- filtering the library by all/blog/pages/assets and searching by title, path, tags, or URL;
- viewing item properties such as type, title, slug, path, public URL, file size, modified time, draft/featured state, and frontmatter fields;
- scanning static local public asset references from Markdown links/images, HTML media `src` attributes, and `heroImage` frontmatter;
- showing which public asset URLs a Markdown item references and which Markdown files reference an asset;
- editing existing blog/page metadata and saving it back to frontmatter while keeping the Markdown body unchanged;
- opening the selected file or containing folder with the system default app;
- copying the selected public URL to the clipboard and the `Public URLs` panel;
- importing `.md` and `.mdx` files as blog posts or pages;
- importing images, PDFs, audio, video, and other files into `public/uploads/`;
- editing title, slug, description, author, date/time, tags, draft, featured, page order, and hero image metadata;
- running `npm run build` and showing output in the log;
- running `git status --short`;
- running `git add .`, `git commit -m`, and `git push` after asking for a commit message;
- opening the public site and GitHub repository in the browser.

The maintenance view does not delete files or bulk rename existing content. Asset rows are read-only; use `Open File`, `Open Folder`, or `Copy Public URL` for asset maintenance.

It uses only the Python standard library. It does not store GitHub tokens and relies on the existing Git configuration on the machine.

Optional executable packaging can be done later with PyInstaller:

```powershell
conda run -n psblog python -m pip install pyinstaller
conda run -n psblog pyinstaller --onefile --windowed --name BlogPublisher tools/blog_publisher/__main__.py
```