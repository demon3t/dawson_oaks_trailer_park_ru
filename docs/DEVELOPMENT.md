# Разработка русификатора

## Структура репозитория

| Путь | Назначение |
| --- | --- |
| `install.bat`, `uninstall.bat` | запуск установки и удаления для пользователя |
| `scripts/installer.ps1` | установщик: применяет патчи из `patch/` к файлам игры |
| `patch/` | бинарные патчи `*.dpatch` и `manifest.json` (хеши оригиналов и результата) |
| `translation/parts/*.json` | перевод: плоские ключи `a.b.c` → строка |
| `tools/extract_originals.py` | копирует оригинальные файлы игры в `original/` и выгружает `en.json` |
| `tools/build.py` | собирает пропатченные файлы в `build/` |
| `tools/make_patch.py` | строит `patch/` как разницу между `original/` и `build/` |

Папки `original/` и `build/` содержат файлы игры и в git не попадают.

## Сборка

```text
pip install -r tools/requirements.txt
python tools/extract_originals.py "D:/SteamLibrary/steamapps/common/Dawson Oaks Trailer Park"
python tools/build.py
python tools/make_patch.py
```

`extract_originals.py` запускать на чистой игре (без русификатора). `build.py` предупреждает
о непереведённых ключах и несовпадающих плейсхолдерах (`{0}`, `<color>`, `[TAB]`).
После сборки коммитятся `translation/` и `patch/`.

## Что меняется в игре

| Файл | Изменение |
| --- | --- |
| `Dawson Oaks Trailer Park_Data/resources.assets` | новый TextAsset `ru` (JSON с переводом); в TMP Settings добавлен глобальный fallback-шрифт с кириллицей |
| `Dawson Oaks Trailer Park_Data/globalgamemanagers` | TextAsset зарегистрирован в Resources как `localization/Русский` |
| `Dawson Oaks Trailer Park_Data/StreamingAssets/default_settings.json` | «Русский» добавлен в конец списка языков |
| `GameAssembly.dll` | 7 байт по смещению `0x70B6B7` (см. ниже) |

Установщик сохраняет оригиналы как `*.bak` и выставляет язык в
`%USERPROFILE%\AppData\LocalLow\Striped Panda Studios\Dawson Oaks Trailer Park\settings.json`.

### Патч GameAssembly.dll

Игра на Unity 6000.3 (IL2CPP, metadata v39). `LocalizationManager.OnSettingsChanged()`
получает название языка из настроек (`"English"`, `"German"`…), через `switch` превращает его
в код (`"en"`, `"de"`…) и грузит `Resources.Load("Localization/" + код)`. Для неизвестных
названий код по умолчанию `"en"`. Патч заменяет это значение по умолчанию на само название:

```text
mov rbx, [rip+…]   ; "en"        48 8B 1D 3A 44 FC 03
→
mov rbx, rdi       ; название    48 8B DF
nop                ;             0F 1F 40 00
```

Существующие языки обрабатываются `switch` как раньше. Пункт «Русский» загружает
`Localization/Русский`, недостающие ключи берутся из английского (fallback игры).

### Шрифты

Почти все TMP-шрифты игры динамические, а их исходные TTF (Impact, Times, LiberationSans,
Joystix, Bulletin) содержат кириллицу, поэтому русские буквы генерируются на лету тем же
шрифтом. Для шрифтов без кириллицы (HandWrittenFont, Sample League, digital-7) в TMP Settings
добавлен глобальный fallback «LiberationSans SDF - Fallback».

## Обновление под новую версию игры

1. Проверить файлы игры в Steam (чтобы были оригиналы) и запустить `extract_originals.py`.
2. Найти место патча: дизассемблировать игру через
   [Cpp2IL](https://github.com/SamboyCoding/Cpp2IL) (`--output-as isil`), открыть метод
   `LocalizationManager.OnSettingsChanged`, найти загрузку литерала `"en"` перед `switch`.
   Обновить `DLL_PATCH_OFFSET` / `DLL_PATCH_OLD` в `tools/build.py`.
3. Если изменились структуры TMP Settings или шрифтов, проверить `TMP_SETTINGS_FALLBACK_OFFSET`
   (`build.py` прервётся с ошибкой, если структура не совпадёт).
4. Добавить перевод для новых ключей (`build.py` выводит их список как «без перевода»).
5. `build.py` → `make_patch.py` → проверить в игре → закоммитить `patch/` и `translation/`.

## Формат .dpatch

```text
"DOTP1"
0x01 <u64 offset> <u32 length>   — скопировать байты из оригинала
0x02 <u32 length> <bytes>        — вставить новые байты
```
