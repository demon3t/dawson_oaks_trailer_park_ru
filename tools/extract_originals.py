"""Копирует оригинальные файлы игры в original/ и выгружает en.json.

Запускать на чистой (не пропатченной) игре:
    python tools/extract_originals.py "D:/SteamLibrary/steamapps/common/Dawson Oaks Trailer Park"
"""
import os
import shutil
import sys

import UnityPy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIG = os.path.join(ROOT, "original")
DATA = "Dawson Oaks Trailer Park_Data"
FILES = {
    "GameAssembly.dll": "GameAssembly.dll",
    "resources.assets": f"{DATA}/resources.assets",
    "globalgamemanagers": f"{DATA}/globalgamemanagers",
    "default_settings.json": f"{DATA}/StreamingAssets/default_settings.json",
}


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    game = sys.argv[1]
    os.makedirs(ORIG, exist_ok=True)
    for name, rel in FILES.items():
        src = os.path.join(game, rel)
        if os.path.exists(src + ".bak"):
            sys.exit(f"Найден {rel}.bak — игра пропатчена. Удалите русификатор или проверьте файлы в Steam.")
        shutil.copyfile(src, os.path.join(ORIG, name))
        print(f"скопирован {name}")

    env = UnityPy.load(os.path.join(ORIG, "resources.assets"))
    for obj in env.objects:
        if obj.type.name == "TextAsset":
            data = obj.read()
            if data.m_Name == "en":
                with open(os.path.join(ORIG, "en.json"), "w", encoding="utf-8") as f:
                    f.write(data.m_Script)
                print("выгружен en.json")
                return
    sys.exit("TextAsset 'en' не найден")


if __name__ == "__main__":
    main()
