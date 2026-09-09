#!/usr/bin/env python3
"""检查并更新 maur 中带有更新元数据的 PKGBUILD。"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def github_json(url: str) -> dict:
    """读取 GitHub API，使用 Actions token 降低公开 API 限流概率。"""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "maur-update-workflow",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def metadata(text: str, key: str) -> str:
    match = re.search(rf"^#\s*{re.escape(key)}:\s*(\S+)\s*$", text, re.MULTILINE)
    if not match:
        raise ValueError(f"缺少 {key} 元数据")
    return match.group(1)


def assignment(text: str, key: str) -> str:
    match = re.search(rf"^{re.escape(key)}=([^\n]+)$", text, re.MULTILINE)
    if not match:
        raise ValueError(f"缺少 {key} 定义")
    return match.group(1).strip().strip("'\"")


def replace_once(text: str, pattern: str, replacement: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise ValueError(f"无法唯一更新模式：{pattern}")
    return updated


def update_srcinfo(path: Path, values: dict[str, str]) -> None:
    """当前 PKGBUILD 只变化版本、Release URL 和校验值，定点更新 .SRCINFO。"""
    if not path.exists():
        raise ValueError(f"缺少 {path.name}，请先执行 makepkg --printsrcinfo")
    text = path.read_text(encoding="utf-8")
    text = replace_once(text, r"^[ \t]+pkgver = .*?$", f"\tpkgver = {values['version']}")
    text = replace_once(text, r"^[ \t]+url = .*?$", f"\turl = {values['release_url']}")
    text = replace_once(text, r"^[ \t]+source = .*?$", f"\tsource = {values['source_url']}")
    text = replace_once(text, r"^[ \t]+sha256sums = .*?$", f"\tsha256sums = {values['sha256']}")
    path.write_text(text, encoding="utf-8")


def update_package(pkgbuild_path: Path) -> bool:
    original = pkgbuild_path.read_text(encoding="utf-8")
    repo = metadata(original, "UpdateRepo")
    tag_prefix = metadata(original, "UpdateTagPrefix")
    asset_template = metadata(original, "UpdateAsset")
    source_template = metadata(original, "UpdateSource")
    pkgname = assignment(original, "pkgname")
    current_version = assignment(original, "pkgver")
    pkgrel = assignment(original, "pkgrel")
    arch = assignment(original, "arch").strip("() ").split()[0].strip("'\"")

    release = github_json(f"https://api.github.com/repos/{repo}/releases/latest")
    if release.get("draft") or release.get("prerelease"):
        raise ValueError(f"最新 Release 不应是 draft/prerelease：{repo}")

    tag = release["tag_name"]
    if not tag.startswith(tag_prefix):
        raise ValueError(f"Release tag {tag!r} 不匹配前缀 {tag_prefix!r}")
    version = tag[len(tag_prefix) :]
    if not re.fullmatch(r"[0-9A-Za-z@._+:%~]+", version):
        raise ValueError(f"Release tag 得到的 pkgver 不合法：{version!r}")

    asset_name = asset_template.format(
        version=version,
        pkgver=version,
        pkgrel=pkgrel,
        arch=arch,
        pkgname=pkgname,
    )
    asset = next((item for item in release["assets"] if item["name"] == asset_name), None)
    if asset is None:
        names = ", ".join(item["name"] for item in release["assets"])
        raise ValueError(f"Release {tag} 找不到资产 {asset_name!r}；已有资产：{names}")
    digest = asset.get("digest", "")
    if not digest.startswith("sha256:"):
        raise ValueError(f"资产没有 GitHub SHA-256 digest：{asset_name}")

    values = {
        "version": version,
        "release_url": release["html_url"],
        "source_url": source_template.format(
            repo=repo,
            tag=tag,
            version=version,
            pkgver=version,
            pkgrel=pkgrel,
            arch=arch,
            pkgname=pkgname,
            asset=asset_name,
        ),
        "sha256": digest.removeprefix("sha256:"),
    }
    updated = replace_once(original, r"^pkgver=.*$", f"pkgver={values['version']}")
    updated = replace_once(updated, r"^url=.*$", f"url='{values['release_url']}'")
    updated = replace_once(updated, r"^source=.*$", f"source=(\"{values['source_url']}\")")
    updated = replace_once(updated, r"^sha256sums=\('[^']*'\)$", f"sha256sums=('{values['sha256']}')")

    if updated == original:
        print(f"{pkgbuild_path.parent}: 已是最新 {current_version}")
        return False

    pkgbuild_path.write_text(updated, encoding="utf-8")
    update_srcinfo(pkgbuild_path.parent / ".SRCINFO", values)
    print(f"{pkgbuild_path.parent}: {current_version} -> {version}")
    return True


def main() -> int:
    changed = 0
    failures: list[str] = []
    for pkgbuild_path in sorted(ROOT.glob("*/PKGBUILD")):
        try:
            if update_package(pkgbuild_path):
                changed += 1
        except Exception as error:  # noqa: BLE001 - 汇总所有包后统一失败
            failures.append(f"{pkgbuild_path.parent}: {error}")

    if failures:
        for failure in failures:
            print(f"错误：{failure}")
        return 1
    print(f"检查完成，更新 {changed} 个软件包")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
