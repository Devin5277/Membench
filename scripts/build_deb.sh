#!/usr/bin/env bash
# 构建 membench 的 .deb 软件包(适用于 openKylin / Debian 系)。
#
# 用法:
#   bash scripts/build_deb.sh
# 产物:
#   dist/membench_0.1.0_all.deb
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="0.1.0"
PKG="membench"
BUILD_DIR="$ROOT/dist/${PKG}_${VERSION}_all"

echo "[1/4] 清理旧构建目录"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/usr/lib/$PKG"
mkdir -p "$BUILD_DIR/usr/bin"

echo "[2/4] 复制包代码与样例数据"
cp -r "$ROOT/membench" "$BUILD_DIR/usr/lib/$PKG/"
rm -rf "$BUILD_DIR/usr/lib/$PKG/membench/__pycache__"

# 生成 /usr/bin/membench 可执行包装脚本
cat > "$BUILD_DIR/usr/bin/$PKG" <<EOF
#!/bin/sh
exec python3 -m membench "\$@"
EOF
chmod 0755 "$BUILD_DIR/usr/bin/$PKG"

echo "[3/4] 写入 DEBIAN/control"
cp "$ROOT/debian/control" "$BUILD_DIR/DEBIAN/control"

echo "[4/4] 使用 dpkg-deb 构建 .deb"
mkdir -p "$ROOT/dist"
dpkg-deb --build "$BUILD_DIR" "$ROOT/dist/${PKG}_${VERSION}_all.deb"

echo "完成: $ROOT/dist/${PKG}_${VERSION}_all.deb"
