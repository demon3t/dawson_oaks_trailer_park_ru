"""Собирает русификатор, добавляющий в игру новый язык «Русский».

Оригинальные файлы берутся из original/, результат пишется в build/:

1. resources.assets
   - новый TextAsset "ru" с русским JSON (английский не трогается);
   - в TMP Settings добавляется глобальный fallback-шрифт
     "LiberationSans SDF - Fallback" (динамический, с кириллицей) для шрифтов,
     в исходных TTF которых нет кириллицы.
2. globalgamemanagers — TextAsset регистрируется в Resources как
   "localization/<LANGUAGE_NAME>".
3. GameAssembly.dll — LocalizationManager.OnSettingsChanged() сопоставляет
   название языка из настроек с кодом файла через switch, а для неизвестных
   названий подставляет "en". Патч заменяет это значение по умолчанию на само
   название, так что пункт "Русский" загружает Resources "Localization/Русский".
   Все существующие языки работают как раньше.
4. default_settings.json — "Русский" добавляется в конец списка языков
   (в конец, чтобы не сдвинуть индексы уже выбранных языков).
"""
import copy
import json
import os
import re
import shutil
import struct
import sys

import UnityPy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIG = os.path.join(ROOT, "original")
RU_DIR = os.path.join(ROOT, "translation", "parts")
OUT_DIR = os.path.join(ROOT, "build")

LANGUAGE_NAME = "Русский"
TEXT_ASSET_NAME = "ru"

# PPtr из resources.assets на "LiberationSans SDF - Fallback":
# file 2 (sharedassets0.assets), pathID 8127
FALLBACK_PPTR = struct.pack("<iq", 2, 8127)
# В TMP Settings список m_fallbackFontAssets лежит сразу после двух bool
# (m_autoSizeTextContainer, m_IsTextObjectScaleStatic), за ним m_matchMaterialPreset.
TMP_SETTINGS_FALLBACK_OFFSET = 0xAC

# OnSettingsChanged: `mov rbx, [rip+X]` (X -> литерал "en") -> `mov rbx, rdi; nop4`
# (rdi = название языка, которое вернул SettingsManager.GetAlternative("language"))
DLL_PATCH_OFFSET = 0x70B6B7
DLL_PATCH_OLD = bytes.fromhex("488b1d3a44fc03")
DLL_PATCH_NEW = bytes.fromhex("488bdf0f1f4000")

PLACEHOLDER_RE = re.compile(r"\{[^}]*\}|<[^>]+>|\[[^\]]+\]")


def load_json(path):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def load_translation():
    ru = {}
    for name in sorted(os.listdir(RU_DIR)):
        if name.endswith(".json"):
            part = load_json(os.path.join(RU_DIR, name))
            dup = set(part) & set(ru)
            if dup:
                sys.exit(f"{name}: повторяющиеся ключи {sorted(dup)}")
            ru.update(part)
    return ru


def translate_tree(node, ru, prefix, stats):
    out = {}
    for k, v in node.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out[k] = translate_tree(v, ru, key, stats)
            continue
        stats["seen"].add(key)
        t = ru.get(key)
        if not t:
            stats["missing"].append(key)
            out[k] = v
            continue
        if sorted(PLACEHOLDER_RE.findall(v)) != sorted(PLACEHOLDER_RE.findall(t)):
            stats["placeholders"].append(key)
        out[k] = t
    return out


def patch_tmp_settings(raw):
    off = TMP_SETTINGS_FALLBACK_OFFSET
    count = struct.unpack_from("<i", raw, off)[0]
    # m_matchMaterialPreset (bool=1) сразу за пустым списком — проверка, что смещение верное
    if count == 0 and struct.unpack_from("<i", raw, off + 4)[0] == 1:
        return raw[:off] + struct.pack("<i", 1) + FALLBACK_PPTR + raw[off + 4:]
    sys.exit(f"TMP Settings: неожиданная структура (count={count}), патч не применён")


def save_env(env, name):
    with open(os.path.join(OUT_DIR, name), "wb") as f:
        f.write(list(env.files.values())[0].save())


def build_resources(ru_json):
    env = UnityPy.load(os.path.join(ORIG, "resources.assets"))
    sf = list(env.files.values())[0]
    template = tmp = None
    for obj in sf.objects.values():
        if obj.type.name == "TextAsset":
            name = obj.read().m_Name
            if name == TEXT_ASSET_NAME:
                sys.exit(f"TextAsset '{TEXT_ASSET_NAME}' уже есть в оригинале")
            if name == "en":
                template = obj
        elif obj.type.name == "MonoBehaviour" and obj.read(check_read=False).m_Name == "TMP Settings":
            tmp = obj
    if not template or not tmp:
        sys.exit("В resources.assets не найдены TextAsset 'en' или TMP Settings")

    new = copy.copy(template)
    new.path_id = max(sf.objects) + 1
    sf.objects[new.path_id] = new
    data = new.read()
    data.m_Name = TEXT_ASSET_NAME
    data.m_Script = ru_json
    data.save()

    tmp.set_raw_data(patch_tmp_settings(tmp.get_raw_data()))
    save_env(env, "resources.assets")
    return new.path_id


def build_globalgamemanagers(path_id):
    env = UnityPy.load(os.path.join(ORIG, "globalgamemanagers"))
    sf = list(env.files.values())[0]
    file_id = 1 + [e.path for e in sf.externals].index("resources.assets")
    for obj in sf.objects.values():
        if obj.type.name == "ResourceManager":
            tree = obj.read_typetree()
            pptr = {"m_FileID": file_id, "m_PathID": path_id}
            # Unity приводит путь к нижнему регистру при поиске; на случай, если
            # кириллица не понижается, регистрируем оба варианта написания.
            keys = {f"localization/{LANGUAGE_NAME.lower()}", f"localization/{LANGUAGE_NAME}"}
            container = [e for e in tree["m_Container"] if e[0] not in keys]
            container += [[k, pptr] for k in sorted(keys)]
            container.sort(key=lambda e: e[0])
            tree["m_Container"] = container
            obj.save_typetree(tree)
            save_env(env, "globalgamemanagers")
            return
    sys.exit("ResourceManager не найден в globalgamemanagers")


def build_dll():
    with open(os.path.join(ORIG, "GameAssembly.dll"), "rb") as f:
        dll = bytearray(f.read())
    o = DLL_PATCH_OFFSET
    if dll[o:o + len(DLL_PATCH_OLD)] != DLL_PATCH_OLD:
        sys.exit("GameAssembly.dll: байты в месте патча не совпадают (другая версия игры)")
    dll[o:o + len(DLL_PATCH_NEW)] = DLL_PATCH_NEW
    with open(os.path.join(OUT_DIR, "GameAssembly.dll"), "wb") as f:
        f.write(dll)


def build_settings():
    with open(os.path.join(ORIG, "default_settings.json"), "rb") as f:
        text = f.read().decode("utf-8-sig")
    m = re.search(r'("language"\s*:\s*\{.*?"alternatives"\s*:\s*\[)(.*?)(\s*\])', text, re.S)
    if not m:
        sys.exit("default_settings.json: не найден список языков")
    items, tail = m.group(2), m.group(3)
    if f'"{LANGUAGE_NAME}"' in items:
        sys.exit("default_settings.json: язык уже есть в оригинале")
    indent = re.search(r"\n(\s*)\"", items).group(1)
    new_items = items.rstrip() + f',\n{indent}"{LANGUAGE_NAME}"'
    text = text[:m.start(2)] + new_items + tail + text[m.end(3):]
    json.loads(text)  # проверка валидности
    with open(os.path.join(OUT_DIR, "default_settings.json"), "wb") as f:
        f.write(b"\xef\xbb\xbf" + text.encode("utf-8"))


def main():
    en = load_json(os.path.join(ORIG, "en.json"))
    ru = load_translation()
    stats = {"missing": [], "placeholders": [], "seen": set()}
    ru_json = json.dumps(translate_tree(en, ru, "", stats), ensure_ascii=False, indent=2)

    if os.path.isdir(OUT_DIR):
        shutil.rmtree(OUT_DIR)
    os.makedirs(OUT_DIR)

    path_id = build_resources(ru_json)
    build_globalgamemanagers(path_id)
    build_dll()
    build_settings()

    print(f"OK: {OUT_DIR} (TextAsset '{TEXT_ASSET_NAME}', pathID {path_id})")
    for k in sorted(set(ru) - stats["seen"]):
        print(f"  ВНИМАНИЕ: ключа нет в en.json: {k}")
    print(f"Переведено: {len(ru)}, без перевода: {len(stats['missing'])}")
    for k in stats["placeholders"]:
        print(f"  ВНИМАНИЕ: не совпадают плейсхолдеры/теги в {k}")


if __name__ == "__main__":
    main()
