# Разработка NeuroMuseLab

## Устройство проекта

`main.py` создаёт `QApplication`, применяет One Dark, задаёт иконку и открывает `MainWindow`. `app/core` управляет отправкой и рабочими потоками, `app/services/telegram_service.py` вызывает Telegram API, `app/services/settings_service.py` сохраняет локальные настройки, `app/ui` содержит форму и масштабируемую тему. Единственный источник версии — `VERSION`; `app/version.py` читает его из исходников или frozen bundle.

## Среда и проверки

На Windows используйте Python 3.12 и проектную `.venv`:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install pytest ruff pyinstaller
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m ruff check . --no-cache
```

Запускайте исходники через `.\.venv\Scripts\python.exe main.py`. Для оконного сборщика используйте `.\.venv\Scripts\pythonw.exe Build_Tools\SpecCompiler.pyw`.

## Локальные данные

`settings.json` хранит токен бота, канал, необязательную ссылку кнопки, выбранные файлы, текст и геометрию окна. Токен записывается без шифрования. `logs/session.log` содержит журнал сессии. Исходники и переносимая сборка используют свой каталог; установленная версия определяется по `installed.marker` и хранит данные каждого пользователя в `%APPDATA%\NeuroMuseLab`. Эти файлы игнорируются Git. В исходниках и примерах нет личной ссылки, токена, путей к файлам или каналов. Пустая ссылка отключает кнопку.

Перед обновлением переносимой папки сохраните её `settings.json` отдельно и перенесите в новую папку после распаковки. Не копируйте этот файл в публичный релиз.

## Сборка Windows

```powershell
.\.venv\Scripts\python.exe Build_Tools\build_release.py
```

`build_release.py` требует именно проектную `.venv` и подменяет унаследованный `PATH` минимальным списком доверенных Python, PySide6 и Windows runtime. `NeuroMuseLab.spec` проверяет каждый источник `Analysis.binaries` и затем ставит в корень `_internal` полный комплект MSVC runtime из PySide6. После сборки проверяются `COLLECT-00.toc`, хэши runtime DLL и отдельный консольный frozen import fixture со stdout/stderr, кодом завершения и timeout. Только после этих ворот `post_build.py` переносит папку в корень проекта.

Сборка копирует только `logo.ico`, `VERSION` и `LICENSE`. `settings.json`, журналы, другие JSON и локальные материалы не копируются. Сборочные скрипты не запускают GUI-приложение автоматически. При существующей корневой папке `NeuroMuseLab/` сборка останавливается: проверьте и сохраните её пользовательские данные до отдельной очистки.

Для установщика сначала создайте проверенную переносимую папку, затем выполните `ISCC.exe Build_Tools\NeuroMuseLab.iss` с Inno Setup 6. Установщик кладёт в каталог приложения только файлы из явного списка и маркер установленной версии; личные данные из исходного каталога в него не попадают. Результат — `release/NeuroMuseLab_v<версия>_Setup.exe`. Мастер установки только на русском языке; каталог по умолчанию — `D:\Apps\NeuroMuseLab` при наличии диска D, иначе `C:\Apps\NeuroMuseLab`. В конце установки пользователь может запустить приложение отмеченным флажком.

## Релиз и публичное дерево

`README.md` и `README.en.md` описывают самостоятельную установку и запуск; `RELEASE_NOTES.md` хранит историю, `LICENSE` применяет MIT к собственному коду. Перед публикацией проверяйте дерево Git, удалённые refs и release assets, чтобы личные настройки и собранные файлы не попадали в исходный код.
