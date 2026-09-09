# maur

这是一个供 `paru` 使用的 Manjaro PKGBUILD 仓库。

GitHub Actions 每 30 分钟检查带有 `UpdateRepo`、`UpdateTagPrefix`、
`UpdateAsset` 和 `UpdateSource` 元数据的包目录。发现上游最新 Release 后，
workflow 会更新 `PKGBUILD`、下载地址、SHA-256 和 `.SRCINFO`，并自动提交回本仓库；
当前只有 `codex-desktop`。

当前包：`codex-desktop`

- 来源：<https://github.com/pygojrc/codex-desktop-linux>
- 固定 Release：`manjaro-kde-26.903.61454`
- 架构：`x86_64`
- 构建方式：在本机 Manjaro 环境中下载上游固定 `.pkg.zst`，校验 SHA-256 后生成本地 pacman 包

## paru 配置

在 `~/.config/paru/paru.conf` 中添加：

```ini
[maur]
Url = https://github.com/pygojrc/maur.git
Depth = 3
```

然后同步并安装：

```bash
paru -Sya
paru -S maur/codex-desktop
```

该仓库是 PKGBUILD 仓库，不是 ArchLinuxCN，也不是 pacman 二进制仓库；包会由 `paru` 在本地构建。

## 更新

上游发布新版本后，maur 的 workflow 会更新 `PKGBUILD` 中的版本、Release 下载地址和
`sha256sums`，同时更新 `.SRCINFO`。
