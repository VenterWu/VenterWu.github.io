# 本地可视化发布器指南

本项目提供一个 Python Tkinter 图形界面工具，用来导入博客内容、管理公开附件，并一键执行构建、提交和推送。工具只使用 Python 标准库，不会保存 GitHub token。

## 启动

在仓库根目录运行：

```powershell
conda run -n psblog python -m tools.blog_publisher
```

查看帮助而不打开窗口：

```powershell
conda run -n psblog python -m tools.blog_publisher --help
```

如果不是从仓库根目录启动，可以加 `--repo`：

```powershell
conda run -n psblog python -m tools.blog_publisher --repo "F:\Project\ProjectForFun\Software\Personal Blog Web"
```

工具会自动寻找包含 `package.json` 和 `astro.config.ts` 的仓库根目录，也可以在界面里点击 `Browse` 手动选择。

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