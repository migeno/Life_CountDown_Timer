#!/usr/bin/env python3
"""元画像から各サイズのアイコンを書き出す。

    python3 tools/make-icons.py <元画像.png>

元画像は「白い余白の中に角丸の正方形が置かれた」形を想定している。
白フチを取り除いたうえで、角丸の外に残る白を背景のグラデーションで
埋めて全面正方形にする（iOS / Android は独自のマスクをかけるため、
アイコン側は角を丸めず全面を塗っておくのが正しい）。

必要: Pillow
"""
import sys, os
from PIL import Image
import numpy as np

OUT = os.path.join(os.path.dirname(__file__), '..', 'icons')
TRIM = 10   # 上下の境界（アンチエイリアス）を避けて内側で切る量
PAD  = 12   # 角を埋めるとき、境界より内側から色を拾う量


def build_master(src, size=1024):
    im = Image.open(src).convert('RGB')
    a = np.array(im)

    # 白フチを除いて角丸の四角に切り出す
    ys, xs = np.where((a < 245).any(axis=2))
    im = im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    im = im.crop((0, TRIM, im.width, im.height - TRIM))

    # 角の白を、境界より内側の色で行ごとに埋める（グラデーションを保つ）
    a = np.array(im).astype(np.uint8)
    nw = (a < 245).any(axis=2)
    for y in range(a.shape[0]):
        row = np.where(nw[y])[0]
        if len(row) == 0:
            continue
        l, r = int(row[0]), int(row[-1])
        if r - l < 2 * PAD:
            a[y, :] = a[y, (l + r) // 2]
            continue
        a[y, :l + PAD]   = a[y, l + PAD]
        a[y, r - PAD + 1:] = a[y, r - PAD]

    full = Image.fromarray(a)
    s = min(full.size)
    full = full.crop(((full.width - s) // 2, (full.height - s) // 2,
                      (full.width - s) // 2 + s, (full.height - s) // 2 + s))
    return full.resize((size, size), Image.LANCZOS)


def build_maskable(master, size=512, inner=410):
    """安全領域（内側80%）に収めた版。
    背景はアートワークと同じ写像で端の列を引き伸ばすので継ぎ目が出ない。"""
    m = np.array(master)
    off = (size - inner) // 2
    col = m[:, 6, :]
    ys = np.clip(((np.arange(size) - off) / inner * (len(col) - 1)).round().astype(int),
                 0, len(col) - 1)
    bg = np.repeat(col[ys][:, None, :], size, axis=1).astype(np.uint8)
    mk = Image.fromarray(bg)
    mk.paste(master.resize((inner, inner), Image.LANCZOS), (off, off))
    return mk


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    os.makedirs(OUT, exist_ok=True)
    master = build_master(sys.argv[1])
    master.save(f'{OUT}/icon-1024.png', optimize=True)
    for n in (512, 192, 180):
        master.resize((n, n), Image.LANCZOS).save(f'{OUT}/icon-{n}.png', optimize=True)
    for n in (32, 16):
        master.resize((n, n), Image.LANCZOS).save(f'{OUT}/favicon-{n}.png', optimize=True)
    build_maskable(master).save(f'{OUT}/icon-maskable-512.png', optimize=True)
    master.resize((48, 48), Image.LANCZOS).save(
        f'{OUT}/../favicon.ico', sizes=[(16, 16), (32, 32), (48, 48)])
    print('wrote icons/ and favicon.ico')


if __name__ == '__main__':
    main()
