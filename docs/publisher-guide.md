# 本地可视化发布器指南

本项目提供一个 Python Tkinter 图形界面工具，用来导入博客内容、管理公开附件，并一键执行构建、提交和推送。工具只使用 Python 标准库，不会保存 GitHub token。

## 启动

推荐使用仓库根目录的启动器。它们会先切换到仓库根目录，再执行 `python -m tools.blog_publisher`，所以 Python 能找到 `tools.blog_publisher` 模块。

方式一：双击或在命令行运行 Windows 启动器：

```cmd
Start-BlogPublisher.cmd
```

方式二：在 PowerShell 里运行启动器：

```powershell
.\Start-BlogPublisher.ps1
```

如果 PowerShell 执行策略阻止脚本，可以使用：

```powershell
powershell -ExecutionPolicy Bypass -File .\Start-BlogPublisher.ps1
```

方式三：手动切到仓库根目录后启动：

```powershell
Set-Location "F:\Project\ProjectForFun\Software\Personal Blog Web"
conda run -n psblog python -m tools.blog_publisher
```

查看帮助而不打开窗口：

```powershell
.\Start-BlogPublisher.ps1 --help
```

不要从任意目录直接运行下面这种命令：

```powershell
conda run -n psblog python -m tools.blog_publisher --repo "F:\Project\ProjectForFun\Software\Personal Blog Web"
```

原因是 Python 会先在当前工作目录和 `PYTHONPATH` 里导入 `tools.blog_publisher`，导入成功后才会解析 `--repo` 参数；如果当前目录不是仓库根目录，就会先报 `ModuleNotFoundError: No module named 'tools'`。除非你手动设置 `PYTHONPATH`，否则请使用根目录启动器，或先 `Set-Location` 到仓库根目录。

工具启动后会自动寻找包含 `package.json` 和 `astro.config.ts` 的仓库根目录，也可以在界面里点击 `Browse` 手动选择。

## 导入文章

1. 点击 `Add Files`，选择 `.md` 或 `.mdx` 文件。
2. 在 `Content type` 选择 `Blog Post`。
3. 编辑 `Title`、`Slug / destination`、`Description`、`Author`、`Date`、`Time`、`Tags`、`Draft`、`Featured`、`Hero image`。
4. 点击 `Import Selected`。

文章会写入 `src/content/blog/<slug>.md`。如果源 Markdown 已有 frontmatter，工具会读取正文并用界面里的字段重新生成符合当前 Astro content schema 的 frontmatter。tags 会写成 YAML array，draft/featured 会写成 boolean。

## 导入页面

1. 点击 `Add Files`，选择 `.md` 或 `.mdx` 文件。
2. 在 `Content type` 选择 `Page`。
3. 编辑 `Title`、`Slug / destination`、`Description`、`Date`、`Time`、`Page order`、`Draft`。
4. 点击 `Import Selected`。

页面会写入 `src/content/pages/<slug>.md`。页面 schema 不包含 author、tags、featured，这些字段不会写入 page frontmatter。

## 导入图片、PDF、音视频和附件

1. 点击 `Add Files`，选择图片、PDF、音频、视频或其他附件。
2. 如果只想导入附件，在 `Content type` 选择 `Asset Only`。
3. 点击 `Import Selected`。

工具会按类型复制到 `public/uploads/`：

- 图片：`public/uploads/images/<year>/`
- PDF 和文档：`public/uploads/files/<year>/`
- 音频：`public/uploads/audio/<year>/`
- 视频：`public/uploads/video/<year>/`
- 其他文件：`public/uploads/files/<year>/`

如果目标文件名已存在，工具会自动追加 `-2`、`-3`，不会覆盖旧文件。界面里的 `Public URLs` 区域会显示可复制的公开路径，例如 `/uploads/images/2026/photo.jpg`。

## 浏览和维护已有内容

工具启动后会自动扫描内容库。点击 `Library` tab 可以查看已有的 blog post、page 和 public asset。表格列包括 `Type`、`Title / Name`、`Date`、`Tags / Kind`、`Draft`、`Path`。

常用操作：

1. 点击 `Refresh Library` 重新扫描 `src/content/blog/`、`src/content/pages/` 和 `public/`。
2. 在 `Filter` 里选择 `All`、`Blog`、`Pages` 或 `Assets`。
3. 在 `Search` 输入标题、路径、tag、kind 或 public URL 片段来筛选。
4. 选中表格中的一行后，右侧会显示属性、public URL、引用关系，并把可编辑的 Markdown frontmatter 填入 `Existing Item Metadata`。

这个维护视图不会自动删除文件，也不会批量重命名已有内容。Asset 项只显示属性和引用关系，不提供 metadata 保存。

## 文件树

左侧 `Repository Tree` 会显示关键目录：

- `src/content`，包括 blog 和 pages Markdown；
- `public`，包括 `public/uploads/` 以及 public 下的常见静态文件，例如 `favicon.svg`、`robots.txt`、图片、文件、音视频等。

点击树里的文件或目录时，右侧属性区会显示路径、类型、大小、修改时间、public URL（如果该文件位于 `public/` 下）以及引用关系（如果它是已扫描的内容项）。

可以使用：

- `Open File`：用系统默认程序打开选中的文件；如果选中目录，则打开目录。
- `Open Folder`：打开选中文件所在目录。
- `Copy Public URL`：把选中 public 文件或内容路由复制到剪贴板，并写入底部 `Public URLs` 区域。

Windows 下工具优先使用 `os.startfile` 打开文件和文件夹；其他环境会回退到浏览器打开本地路径。

## 引用关系

刷新内容库时，工具会做本地静态引用分析：

- 从 Markdown 正文识别图片和链接，例如 `![alt](/uploads/...)`、`[text](/files/...)`、`[text](/uploads/...)`。
- 从 HTML 片段识别 `<img src="...">`、`<video src="...">`、`<audio src="...">` 和 `<source src="...">`。
- 从 frontmatter 的 `heroImage` 识别 public URL。

选中 blog/page 时，`References` 会列出它引用的 public asset URL。选中 asset 时，`Referenced by` 会列出引用它的 Markdown 文件路径。

引用扫描只分析本地静态 public 路径，不解析外部 URL，也不会下载远程资源。

## 编辑已有文章属性

在 `Library` tab 中选中 blog post 或 page 后，可以在 `Existing Item Metadata` 区编辑已有 Markdown 的 frontmatter 字段。

Blog post 支持保存：

- `Title`
- `Description`
- `Author`
- `Date` / `Time`，写入 `pubDate`
- `Tags`
- `Hero image`
- `Draft`
- `Featured`

Page 支持保存：

- `Title`
- `Description`
- `Date` / `Time`，写入 `updatedDate`
- `Page order`
- `Draft`

点击 `Save Metadata` 后，工具只重写 frontmatter，正文内容保持不变。如果保存失败，例如 description 不满足当前 Astro schema 长度、日期或 page order 无效，工具会用弹窗和底部日志显示原因。

如需修改正文，点击 `Open File` 用默认编辑器打开 Markdown 文件。

## 构建、提交和推送

导入内容后建议先点击 `Run Build`。工具会执行：

```powershell
npm run build
```

构建日志会显示在窗口底部。如果构建失败，先根据日志修复 frontmatter、链接或内容问题。

确认无误后点击 `Git Status` 查看改动，再点击 `Commit & Push`。工具会要求输入 commit message，然后依次执行：

```powershell
git add .
git commit -m "你的提交信息"
git push
```

推送后 GitHub Actions 会负责部署 GitHub Pages。

## 隐私和安全注意事项

- 不要把私密照片、证件、合同、token、`.env`、草稿资料或不想公开的附件导入 `public/`。
- `public/uploads/` 里的文件会成为公开可访问资源。
- 工具不会保存 GitHub token，只使用本机已有的 Git 登录状态或凭据管理器。
- 工具不会自动删除文件，也不会手动绕过 `.gitignore` 添加 `node_modules`、`dist`、`.astro`。
- 对未完成内容使用 `Draft`，并在发布前运行 `Run Build` 验证。