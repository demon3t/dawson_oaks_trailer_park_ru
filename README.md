# Русификатор Dawson Oaks Trailer Park

Русский язык для игры [Dawson Oaks Trailer Park](https://store.steampowered.com/app/3640200/Dawson_Oaks_Trailer_Park/) (Steam).
Устанавливается одной командой и добавляет в настройки игры новый язык «Русский».
Переведены меню, настройки, роли, позывы, подсказки, предметы, телефон и обучение.

> **English:** Russian translation (localization mod) for Dawson Oaks Trailer Park.
> Adds a new “Русский” language to the game settings; all original languages stay intact.

## Как установить

1. Закройте игру, если она запущена.
2. Откройте PowerShell: нажмите **Win + X** и выберите **Терминал** (или **Windows PowerShell**).
3. Вставьте эту команду и нажмите **Enter**:

   ```powershell
   irm https://raw.githubusercontent.com/demon3t/dawson_oaks_trailer_park_ru/main/install.ps1 | iex
   ```

4. Дождитесь надписи «Готово!» и запустите игру.

Если язык не переключился сам, выберите его вручную: **Settings → Game → Language → Русский**.

## Как удалить

Так же откройте PowerShell и выполните:

```powershell
irm https://raw.githubusercontent.com/demon3t/dawson_oaks_trailer_park_ru/main/uninstall.ps1 | iex
```

Игра вернётся к исходному состоянию.

## Установка без команды

1. Нажмите зелёную кнопку **Code** вверху страницы и выберите **Download ZIP**.
2. Распакуйте архив и запустите **`install.bat`**. Для удаления запустите **`uninstall.bat`**.

## Если что-то пошло не так

- **«Игра не найдена»**: укажите папку игры сами. Найти её можно в Steam:
  правый клик по игре → **Управление** → **Просмотреть локальные файлы**. Затем выполните команду,
  подставив свой путь:

  ```powershell
  & ([scriptblock]::Create((irm https://raw.githubusercontent.com/demon3t/dawson_oaks_trailer_park_ru/main/install.ps1))) -GameDir "D:\SteamLibrary\steamapps\common\Dawson Oaks Trailer Park"
  ```

  Или скачайте ZIP и перетащите папку игры мышкой на `install.bat`.
- **Появился запрос прав администратора**: это нормально, если игра установлена в `Program Files`. Нажмите «Да».
- **«Файл не подходит к этой версии русификатора»**: игра обновилась. Дождитесь обновления
  русификатора и установите его заново той же командой.
- **После обновления игры пропал русский язык**: это нормально, Steam заменяет файлы игры.
  Выполните команду установки ещё раз.
- **Игра сломалась**: выполните команду удаления или в Steam: правый клик по игре →
  **Свойства** → **Установленные файлы** → **Проверить целостность файлов игры**.

## Важно

- Это неофициальный фанатский перевод.
- Русификатор меняет только язык интерфейса, остальные языки игры остаются на месте.
- Нашли ошибку в переводе или текст не помещается? Создайте issue со скриншотом.

---

Для разработчиков: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

**Ключевые слова:** Dawson Oaks Trailer Park русификатор, Dawson Oaks Trailer Park на русском,
русский язык, перевод, локализация, rusifikator, Russian translation, Russian localization.

#DawsonOaksTrailerPark #DawsonOaks #русификатор #русскийязык #перевод #локализация #русификаторигр #Steam #rusifikator #RussianTranslation
