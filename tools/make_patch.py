"""Создаёт бинарные патчи (original/ -> build/) для установщика.

Формат файла .dpatch:
    b"DOTP1"
    далее операции до конца файла:
        0x01 <u64 offset> <u32 length>   — скопировать байты из оригинала
        0x02 <u32 length> <bytes>        — вставить новые байты

В патч попадают только изменённые участки, поэтому в репозитории нет файлов игры.
Пишет patch/*.dpatch и patch/manifest.json (пути, SHA-256 оригинала и результата).
"""
import hashlib
import json
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIG = os.path.join(ROOT, "original")
BUILD = os.path.join(ROOT, "build")
OUT = os.path.join(ROOT, "patch")

# имя файла -> путь относительно папки игры
FILES = {
    "GameAssembly.dll": "GameAssembly.dll",
    "resources.assets": "Dawson Oaks Trailer Park_Data/resources.assets",
    "globalgamemanagers": "Dawson Oaks Trailer Park_Data/globalgamemanagers",
    "default_settings.json": "Dawson Oaks Trailer Park_Data/StreamingAssets/default_settings.json",
}

BLOCK = 32
MAGIC = b"DOTP1"


def sha256(data):
    return hashlib.sha256(data).hexdigest().upper()


def match_len(old, o, new, n):
    """Длина совпадения old[o:] и new[n:] (быстро, кусками)."""
    length, step = 0, 1 << 16
    limit = min(len(old) - o, len(new) - n)
    while step:
        while length + step <= limit and old[o + length:o + length + step] == new[n + length:n + length + step]:
            length += step
        step >>= 1
    return length


def diff(old, new):
    index = {}
    for off in range(0, len(old) - BLOCK + 1, BLOCK):
        index.setdefault(old[off:off + BLOCK], off)

    ops, literal = [], bytearray()
    p = 0
    while p < len(new):
        o = index.get(new[p:p + BLOCK]) if p + BLOCK <= len(new) else None
        if o is None:
            literal.append(new[p])
            p += 1
            continue
        # расширяем совпадение назад за счёт накопленного литерала
        while literal and o > 0 and old[o - 1] == literal[-1]:
            literal.pop()
            o -= 1
            p -= 1
        length = match_len(old, o, new, p)
        if literal:
            ops.append((2, bytes(literal)))
            literal = bytearray()
        ops.append((1, o, length))
        p += length
    if literal:
        ops.append((2, bytes(literal)))
    return ops


def encode(ops):
    out = bytearray(MAGIC)
    for op in ops:
        if op[0] == 1:
            out += struct.pack("<BQI", 1, op[1], op[2])
        else:
            out += struct.pack("<BI", 2, len(op[1])) + op[1]
    return bytes(out)


def apply(old, patch):
    assert patch[:len(MAGIC)] == MAGIC
    out, p = bytearray(), len(MAGIC)
    while p < len(patch):
        if patch[p] == 1:
            o, n = struct.unpack_from("<QI", patch, p + 1)
            out += old[o:o + n]
            p += 13
        else:
            n = struct.unpack_from("<I", patch, p + 1)[0]
            out += patch[p + 5:p + 5 + n]
            p += 5 + n
    return bytes(out)


def main():
    os.makedirs(OUT, exist_ok=True)
    manifest = {"files": []}
    for name, game_path in FILES.items():
        with open(os.path.join(ORIG, name), "rb") as f:
            old = f.read()
        with open(os.path.join(BUILD, name), "rb") as f:
            new = f.read()
        patch = encode(diff(old, new))
        if apply(old, patch) != new:
            sys.exit(f"{name}: проверка патча не прошла")
        patch_name = name + ".dpatch"
        with open(os.path.join(OUT, patch_name), "wb") as f:
            f.write(patch)
        manifest["files"].append({
            "name": name,
            "path": game_path,
            "patch": patch_name,
            "original_sha256": sha256(old),
            "patched_sha256": sha256(new),
        })
        print(f"{name}: патч {len(patch):,} байт")
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"OK: {OUT}")


if __name__ == "__main__":
    main()
