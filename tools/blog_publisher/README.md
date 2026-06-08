# Blog Publisher Tool

This folder contains a local Tkinter GUI for importing Markdown and public assets into the Astro blog, then running the build and Git publish commands.

Start it from the repository root:

```powershell
conda run -n psblog python -m tools.blog_publisher
```

Show command-line help without opening the GUI:

```powershell
conda run -n psblog python -m tools.blog_publisher --help
```

The GUI supports:

- importing `.md` and `.mdx` files as blog posts or pages;
- importing images, PDFs, audio, video, and other files into `public/uploads/`;
- editing title, slug, description, author, date/time, tags, draft, featured, page order, and hero image metadata;
- running `npm run build` and showing output in the log;
- running `git status --short`;
- running `git add .`, `git commit -m`, and `git push` after asking for a commit message;
- opening the public site and GitHub repository in the browser.

It uses only the Python standard library. It does not store GitHub tokens and relies on the existing Git configuration on the machine.

Optional executable packaging can be done later with PyInstaller:

```powershell
conda run -n psblog python -m pip install pyinstaller
conda run -n psblog pyinstaller --onefile --windowed --name BlogPublisher tools/blog_publisher/__main__.py
```