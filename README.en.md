<p align="center"><img src="assets/logo.png" width="112" alt="NeuroMuseLab icon"></p>
<h1 align="center">NeuroMuseLab</h1>
<p align="center">Publish one or more MP3 files to a Telegram channel through your own bot.</p>
<p align="center"><a href="README.md">Русский</a> · <a href="https://github.com/Frommer-droid/NeuroMuseLab-App-Public/releases/latest">Latest release</a></p>

NeuroMuseLab is a desktop app for Telegram channel owners. It checks the bot's access, sends tracks in sequence, and can add a cover, text, and a button with your own link.

## Quick start

1. Download `NeuroMuseLab_v0.7.0_Setup.exe` from the [latest release](https://github.com/Frommer-droid/NeuroMuseLab-App-Public/releases/latest) and install the app.
2. Create a bot with `@BotFather`, add it as a channel administrator, and grant permission to post messages.
3. Enter the bot token and the channel's `@username` or numeric `chat_id`. Click “Проверить доступ” (Check access).
4. Choose MP3 files, optionally add a cover and text, then click “Опубликовать пост” (Publish post).

The button link is optional. Leave it blank to post without a donation button. Its value is stored only in the local `settings.json`.

## Features

- One track or multiple tracks sent as separate audio messages.
- One cover before the audio and text after it when a cover is selected.
- Automatic splitting of long text to fit Telegram limits.
- Background sending and saved form fields and interface scale.

## Run from source

The verified development environment is Windows with Python 3.12. The code requires Python 3.10 or newer.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

To build the portable folder, install PyInstaller in the same `.venv` and run:

```powershell
.\.venv\Scripts\python.exe -m pip install pyinstaller
.\.venv\Scripts\python.exe Build_Tools\build_release.py
```

The build checks native DLL origins and runs a separate non-interactive frozen import smoke test. The resulting folder is `NeuroMuseLab/` at the project root. See [DEVELOPER.md](DEVELOPER.md) for details.

## Local data and limitations

The app stores the bot token, channel, link, recent files, and window state in `settings.json` **without encryption**. Installed copies keep personal data in `%APPDATA%\NeuroMuseLab`; source and portable copies keep it beside the executable. `logs/session.log` uses the same location. Protect these files and do not share them. Git and the release build exclude both.

Posting requires internet access, a bot allowed to post in the channel, and access to the Telegram API. Audio files must be `.mp3`. See [RELEASE_NOTES.md](RELEASE_NOTES.md) for version history.

The project's own code is available under the [MIT license](LICENSE); third-party dependencies keep their respective licenses.
