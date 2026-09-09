# maur

`maur` 是供 `paru` 使用的多包 Manjaro PKGBUILD 仓库。

每个一级子目录代表一个软件包，例如 `codex-desktop/`。包目录中的
`PKGBUILD` 可以通过 `UpdateRepo`、`UpdateTagPrefix`、`UpdateAsset` 和
`UpdateSource` 注释声明上游 Release。GitHub Actions 每 30 分钟检查这些包，
发现版本变化后自动更新对应的 `PKGBUILD` 和 `.SRCINFO`。

当前包：

- `codex-desktop`：跟踪 <https://github.com/pygojrc/codex-desktop-linux> 的固定 Release

## paru 配置

在 `~/.config/paru/paru.conf` 中添加：

```ini
[maur]
Url = https://github.com/pygojrc/maur.git
Depth = 3
```

同步并安装：

```bash
paru -Sya
paru -S maur/codex-desktop
```

这是 PKGBUILD 仓库，不是 ArchLinuxCN，也不是 pacman 二进制仓库。
