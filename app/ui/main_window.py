from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QCloseEvent, QScreen, QShowEvent
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.config.constants import MAX_AUDIO_CAPTION_LENGTH, MAX_TEXT_MESSAGE_LENGTH
from app.core.upload_manager import UploadManager
from app.core.workers import PostUploadWorker, VerifyWorker
from app.models.settings import AppSettings
from app.models.upload import UploadResult
from app.services import ui_scale_service
from app.services.session_logger import SessionLogger
from app.services.settings_service import SettingsService
from app.ui.audio_files_widget import AudioFilesWidget
from app.ui.theme import apply_theme, enforce_button_proportions
from app.utils.text_utils import normalize_text
from app.version import __version__


class MainWindow(QMainWindow):
    _LOG_VISIBLE_LINES = 3
    _BASE_MIN_WINDOW_WIDTH = 720
    _BASE_MIN_WINDOW_HEIGHT = 560
    _SCALE_DELTAS = tuple(range(-50, 51, 10))

    def __init__(
        self,
        *,
        settings: AppSettings,
        settings_service: SettingsService,
        logger: SessionLogger,
        upload_manager: UploadManager,
    ) -> None:
        super().__init__()
        self._settings = settings
        self._settings_service = settings_service
        self._logger = logger
        self._upload_manager = upload_manager

        self._busy_mode = ""
        self._verify_worker: VerifyWorker | None = None
        self._post_worker: PostUploadWorker | None = None

        self._screen_tracking_initialized = False
        self._active_screen: QScreen | None = None

        self._setup_ui()
        self._load_settings_to_ui()
        self._append_log(self._logger.info("Приложение запущено."))

    def _setup_ui(self) -> None:
        self.setWindowTitle(f"NeuroMuseLab v{__version__} - Загрузчик аудио в Telegram")

        root = QWidget(self)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(10)

        root_layout.addWidget(self._build_telegram_group())
        root_layout.addWidget(self._build_single_tab(), 1)

        self.log_output = QPlainTextEdit(self)
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("Лог операций")
        self._apply_log_height_limit()
        root_layout.addWidget(self.log_output, 0)

        self.setCentralWidget(root)
        self._setup_scale_controls()
        self.statusBar().showMessage("Готово")

    def _setup_scale_controls(self) -> None:
        self.scale_label = QLabel("Масштаб:", self)
        self.scale_combo = QComboBox(self)
        self.scale_combo.setObjectName("ui_scale_combo")

        for delta in self._SCALE_DELTAS:
            display = "100%" if delta == 0 else f"{delta:+d}%"
            self.scale_combo.addItem(display, delta)

        self.scale_combo.currentIndexChanged.connect(self._on_scale_delta_changed)
        self.statusBar().addPermanentWidget(self.scale_label)
        self.statusBar().addPermanentWidget(self.scale_combo)

    def _build_telegram_group(self) -> QGroupBox:
        box = QGroupBox("Подключение к Telegram", self)
        form = QFormLayout(box)

        self.bot_token_edit = QLineEdit(self)
        self.bot_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.bot_token_edit.setPlaceholderText("Токен от @BotFather")
        form.addRow("Токен бота:", self.bot_token_edit)

        channel_layout = QHBoxLayout()
        self.channel_id_edit = QLineEdit(self)
        self.channel_id_edit.setPlaceholderText("@my_channel или -100...")
        channel_layout.addWidget(self.channel_id_edit, 1)

        self.verify_button = QPushButton("Проверить доступ", self)
        self.verify_button.setObjectName("standard_button")
        self.verify_button.clicked.connect(self._start_verify)
        channel_layout.addWidget(self.verify_button)
        form.addRow("Канал:", channel_layout)

        self.donation_url_edit = QLineEdit(self)
        self.donation_url_edit.setPlaceholderText("Необязательно: https://example.com/donate")
        self.donation_url_edit.textChanged.connect(self._update_poem_hint)
        form.addRow("Ссылка для доната:", self.donation_url_edit)
        return box

    def _build_single_tab(self) -> QWidget:
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        audio_title = QLabel("Аудиофайлы для публикации:", self)
        layout.addWidget(audio_title)

        self.audio_files_widget = AudioFilesWidget(self)
        self.audio_files_widget.files_changed.connect(self._update_poem_hint)
        layout.addWidget(self.audio_files_widget)

        cover_row = QHBoxLayout()
        self.single_cover_edit = QLineEdit(self)
        self.single_cover_edit.setPlaceholderText("Обложка 16:9 (опционально): JPG/PNG/WEBP")
        self.single_cover_edit.textChanged.connect(self._update_poem_hint)
        cover_row.addWidget(self.single_cover_edit, 1)

        cover_browse_button = QPushButton("Обложка", self)
        cover_browse_button.setObjectName("standard_button")
        cover_browse_button.clicked.connect(self._choose_single_cover)
        cover_row.addWidget(cover_browse_button)
        self._single_cover_browse_button = cover_browse_button
        layout.addLayout(cover_row)

        poem_title = QLabel("Стихотворение для публикации:", self)
        layout.addWidget(poem_title)

        self.poem_text_edit = QPlainTextEdit(self)
        self.poem_text_edit.setPlaceholderText("Вставьте стихотворение")
        self.poem_text_edit.textChanged.connect(self._update_poem_hint)
        layout.addWidget(self.poem_text_edit, 1)

        self.poem_hint_label = QLabel("", self)
        self.poem_hint_label.setWordWrap(True)
        layout.addWidget(self.poem_hint_label)

        action_row = QHBoxLayout()

        self.single_publish_button = QPushButton("Опубликовать пост", self)
        self.single_publish_button.setObjectName("primaryButton")
        self.single_publish_button.clicked.connect(self._start_post_upload)
        action_row.addWidget(self.single_publish_button)

        self.single_clear_button = QPushButton("Очистить поля", self)
        self.single_clear_button.setObjectName("danger_btn")
        self.single_clear_button.clicked.connect(self._clear_post_fields)
        action_row.addWidget(self.single_clear_button)

        layout.addLayout(action_row)
        return tab

    def _apply_log_height_limit(self) -> None:
        line_spacing = self.log_output.fontMetrics().lineSpacing()
        frame = self.log_output.frameWidth() * 2
        margins = self.log_output.contentsMargins()
        vertical_margins = margins.top() + margins.bottom()
        padding = max(4, round(line_spacing * 0.35))

        target_height = (line_spacing * self._LOG_VISIBLE_LINES) + frame + vertical_margins + padding
        self.log_output.setMinimumHeight(target_height)
        self.log_output.setMaximumHeight(target_height)

    def _choose_single_cover(self) -> None:
        start_dir = str(Path(self.single_cover_edit.text()).parent) if self.single_cover_edit.text() else ""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Выбор обложки 16:9",
            start_dir,
            "Изображения (*.jpg *.jpeg *.png *.webp)",
        )
        if file_name:
            self.single_cover_edit.setText(file_name)
            self._update_poem_hint()

    def _update_poem_hint(self) -> None:
        text = normalize_text(self.poem_text_edit.toPlainText())
        length = len(text)
        has_cover = bool(self.single_cover_edit.text().strip())
        audio_count = len(self.audio_files_widget.file_paths())

        if audio_count > 1:
            prefix = f"Выбрано {audio_count} аудио. "
            if length == 0:
                if has_cover:
                    self.poem_hint_label.setText(
                        prefix
                        + "Сначала отправится одна обложка с кнопкой доната, затем каждое аудио отдельным сообщением с кнопкой доната."
                    )
                else:
                    self.poem_hint_label.setText(
                        prefix + "Каждое аудио будет отправлено отдельным сообщением с кнопкой доната."
                    )
                return

            if length <= MAX_TEXT_MESSAGE_LENGTH:
                self.poem_hint_label.setText(
                    f"Символов: {length}. После {audio_count} аудио стихотворение будет отправлено один раз "
                    "отдельным сообщением."
                )
            else:
                self.poem_hint_label.setText(
                    f"Символов: {length}. После {audio_count} аудио стихотворение будет разбито "
                    "на несколько сообщений."
                )
            return

        if has_cover:
            if length == 0:
                self.poem_hint_label.setText(
                    "Символов: 0. При обложке сначала отправится изображение, затем аудио без текста стихотворения."
                )
                return

            if length <= MAX_TEXT_MESSAGE_LENGTH:
                self.poem_hint_label.setText(
                    f"Символов: {length}. При обложке стихотворение отправляется отдельным сообщением после аудио."
                )
            else:
                self.poem_hint_label.setText(
                    f"Символов: {length}. Лимит текста в сообщении {MAX_TEXT_MESSAGE_LENGTH}. "
                    "Стихотворение будет разбито на несколько сообщений."
                )
            return

        if length <= MAX_AUDIO_CAPTION_LENGTH:
            self.poem_hint_label.setText(
                f"Символов: {length}. Без обложки стихотворение будет отправлено в подпись к аудио."
            )
            return

        self.poem_hint_label.setText(
            f"Символов: {length}. Лимит подписи к аудио {MAX_AUDIO_CAPTION_LENGTH}. "
            "Стихотворение будет отправлено отдельными сообщениями."
        )

    def _start_verify(self) -> None:
        if self._busy_mode:
            return

        token = self.bot_token_edit.text().strip()
        channel_id = self.channel_id_edit.text().strip()
        self._set_busy("verify")
        self.statusBar().showMessage("Проверка доступа...")

        self._verify_worker = VerifyWorker(self._upload_manager, token, channel_id)
        self._verify_worker.log_message.connect(self._append_log)
        self._verify_worker.finished_ok.connect(self._on_verify_finished)
        self._verify_worker.failed.connect(self._on_worker_failed)
        self._verify_worker.start()

    def _start_post_upload(self) -> None:
        if self._busy_mode:
            return

        token = self.bot_token_edit.text().strip()
        channel_id = self.channel_id_edit.text().strip()
        donation_url = self.donation_url_edit.text().strip()
        file_paths = [Path(path) for path in self.audio_files_widget.file_paths()]
        cover_raw = self.single_cover_edit.text().strip()
        cover_path = Path(cover_raw) if cover_raw else None
        poem_text = self.poem_text_edit.toPlainText()

        self._set_busy("post")
        self.statusBar().showMessage("Публикация поста...")

        self._post_worker = PostUploadWorker(
            manager=self._upload_manager,
            token=token,
            channel_id=channel_id,
            donation_url=donation_url,
            file_paths=file_paths,
            cover_path=cover_path,
            poem_text=poem_text,
        )
        self._post_worker.log_message.connect(self._append_log)
        self._post_worker.finished_ok.connect(self._on_post_finished)
        self._post_worker.failed.connect(self._on_worker_failed)
        self._post_worker.start()

    def _clear_post_fields(self) -> None:
        if self._busy_mode:
            return

        self.audio_files_widget.clear()
        self.single_cover_edit.clear()
        self.poem_text_edit.clear()
        self._update_poem_hint()

    def _on_verify_finished(self, bot_name: str) -> None:
        self._set_busy("")
        self.statusBar().showMessage("Доступ подтвержден", 3000)
        QMessageBox.information(self, "Telegram", f"Подключение успешно.\nБот: {bot_name}")

    def _on_post_finished(self, result: UploadResult) -> None:
        self._set_busy("")
        self.statusBar().showMessage("Пост опубликован", 3000)
        text = (
            f"Пост опубликован.\nАудиофайлов: {result.audio_count}\n"
            f"message_id: {result.message_id}"
        )
        if result.extra_text_messages:
            text += f"\nДоп. сообщений со стихом: {result.extra_text_messages}"
        QMessageBox.information(self, "Готово", text)

    def _on_worker_failed(self, error_text: str) -> None:
        line = self._logger.error(f"Ошибка фоновой задачи: {error_text}")
        self._append_log(line)
        self._set_busy("")
        self.statusBar().showMessage("Ошибка выполнения", 4000)
        QMessageBox.critical(self, "Ошибка", error_text)

    def _set_busy(self, mode: str) -> None:
        self._busy_mode = mode
        is_busy = bool(mode)

        self.verify_button.setEnabled(not is_busy)
        self.donation_url_edit.setEnabled(not is_busy)
        self.single_publish_button.setEnabled(not is_busy)
        self.single_clear_button.setEnabled(not is_busy)
        self.audio_files_widget.set_inputs_enabled(not is_busy)
        self.single_cover_edit.setEnabled(not is_busy)
        self._single_cover_browse_button.setEnabled(not is_busy)
        self.scale_combo.setEnabled(not is_busy)

    def _append_log(self, message: str) -> None:
        self.log_output.appendPlainText(message)

    def _load_settings_to_ui(self) -> None:
        self.bot_token_edit.setText(self._settings.bot_token)
        self.channel_id_edit.setText(self._settings.channel_id)
        self.donation_url_edit.setText(self._settings.donation_url)
        self.audio_files_widget.set_file_paths(self._settings.audio_files)
        self.single_cover_edit.setText(self._settings.single_cover_file)
        self.poem_text_edit.setPlainText(self._settings.poem_text)

        self._settings.ui_scale_mode = "auto"
        self._settings.ui_scale_delta_percent = ui_scale_service.normalize_delta_percent(
            self._settings.ui_scale_delta_percent
        )
        self._set_scale_combo_delta(self._settings.ui_scale_delta_percent)

        has_saved_settings = self._settings_service.has_saved_settings()
        has_valid_geometry = has_saved_settings and self._has_valid_saved_geometry()

        if has_valid_geometry:
            self.resize(
                max(self._BASE_MIN_WINDOW_WIDTH, self._settings.window.width),
                max(self._BASE_MIN_WINDOW_HEIGHT, self._settings.window.height),
            )
            self.move(self._settings.window.x, self._settings.window.y)
            if self._settings.window.maximized:
                self.setWindowState(self.windowState() | Qt.WindowState.WindowMaximized)

        self._recalculate_and_apply_scale(force_window_resize=not has_valid_geometry)
        self._update_poem_hint()

    def _save_ui_to_settings(self) -> None:
        self._settings.bot_token = self.bot_token_edit.text().strip()
        self._settings.channel_id = self.channel_id_edit.text().strip()
        self._settings.donation_url = self.donation_url_edit.text().strip()
        self._settings.audio_files = self.audio_files_widget.file_paths()
        self._settings.single_file = self._settings.audio_files[0] if self._settings.audio_files else ""
        self._settings.single_cover_file = self.single_cover_edit.text().strip()
        self._settings.poem_text = self.poem_text_edit.toPlainText()
        self._settings.ui_scale_mode = "auto"
        self._settings.ui_scale_delta_percent = ui_scale_service.normalize_delta_percent(
            self._settings.ui_scale_delta_percent
        )
        self._settings.ui_scale_percent = ui_scale_service.clamp_int(
            int(self._settings.ui_scale_percent),
            ui_scale_service.MIN_FINAL_UI_SCALE_PERCENT,
            ui_scale_service.MAX_FINAL_UI_SCALE_PERCENT,
        )

        geometry = self.normalGeometry() if self.isMaximized() else self.geometry()
        self._settings.window.x = int(geometry.x())
        self._settings.window.y = int(geometry.y())
        self._settings.window.width = int(geometry.width())
        self._settings.window.height = int(geometry.height())
        self._settings.window.maximized = self.isMaximized()

    def _set_scale_combo_delta(self, delta_percent: int) -> None:
        normalized_delta = ui_scale_service.normalize_delta_percent(delta_percent)
        index = self.scale_combo.findData(normalized_delta)
        if index < 0:
            index = self.scale_combo.findData(0)
        self.scale_combo.blockSignals(True)
        self.scale_combo.setCurrentIndex(max(0, index))
        self.scale_combo.blockSignals(False)

    def _on_scale_delta_changed(self, index: int) -> None:
        delta = self.scale_combo.itemData(index)
        if delta is None:
            return

        normalized_delta = ui_scale_service.normalize_delta_percent(int(delta))
        if normalized_delta == self._settings.ui_scale_delta_percent:
            return

        self._settings.ui_scale_mode = "auto"
        self._settings.ui_scale_delta_percent = normalized_delta
        self._recalculate_and_apply_scale(force_window_resize=True)
        self.statusBar().showMessage(f"Масштаб применен: {self._settings.ui_scale_percent}%", 2500)

    def _current_screen(self) -> QScreen | None:
        handle = self.windowHandle()
        if handle and handle.screen():
            return handle.screen()

        app = QApplication.instance()
        if app is not None:
            return app.primaryScreen()
        return None

    def _recalculate_and_apply_scale(self, *, force_window_resize: bool) -> None:
        screen = self._current_screen()
        if screen is None:
            return

        available = screen.availableGeometry()
        scale_state = ui_scale_service.compute_ui_scale(
            width=available.width(),
            height=available.height(),
            logical_dpi=screen.logicalDotsPerInch(),
            delta_percent=self._settings.ui_scale_delta_percent,
        )
        self._settings.ui_scale_percent = scale_state.final_percent

        app = QApplication.instance()
        if app is not None:
            apply_theme(app, scale_state.scale_factor)
            enforce_button_proportions(self)

        minimum_width = max(560, round(self._BASE_MIN_WINDOW_WIDTH * scale_state.scale_factor))
        minimum_height = max(420, round(self._BASE_MIN_WINDOW_HEIGHT * scale_state.scale_factor))
        self.setMinimumSize(minimum_width, minimum_height)

        self._apply_log_height_limit()

        if force_window_resize and not self.isMaximized():
            self._apply_scaled_window_geometry(screen)

    def _apply_scaled_window_geometry(self, screen: QScreen) -> None:
        available = screen.availableGeometry()
        target_width = min(self.minimumWidth(), available.width())
        target_height = ui_scale_service.calculate_target_window_height(
            available_height=available.height(),
            minimum_height=self.minimumHeight(),
            delta_percent=self._settings.ui_scale_delta_percent,
        )
        current = self.geometry()
        target_x, target_y = ui_scale_service.clamp_window_position(
            x=current.x(),
            y=current.y(),
            width=target_width,
            height=target_height,
            available_x=available.x(),
            available_y=available.y(),
            available_width=available.width(),
            available_height=available.height(),
        )
        self.setGeometry(target_x, target_y, target_width, target_height)

    def _has_valid_saved_geometry(self) -> bool:
        width = int(self._settings.window.width)
        height = int(self._settings.window.height)
        if width <= 0 or height <= 0:
            return False

        rect = QRect(
            int(self._settings.window.x),
            int(self._settings.window.y),
            width,
            height,
        )
        app = QApplication.instance()
        if app is None:
            return True

        screens = app.screens()
        if not screens:
            return True

        return any(screen.availableGeometry().intersects(rect) for screen in screens)

    def _initialize_screen_tracking(self) -> None:
        if self._screen_tracking_initialized:
            return

        handle = self.windowHandle()
        if handle is not None:
            handle.screenChanged.connect(self._on_window_screen_changed)

        app = QApplication.instance()
        if app is not None:
            app.primaryScreenChanged.connect(self._on_app_screen_event)
            app.screenAdded.connect(self._on_app_screen_event)
            app.screenRemoved.connect(self._on_app_screen_event)

        self._screen_tracking_initialized = True
        self._on_window_screen_changed(self._current_screen())

    def _on_window_screen_changed(self, screen: QScreen | None) -> None:
        next_screen = screen or self._current_screen()
        if next_screen is self._active_screen:
            self._recalculate_and_apply_scale(force_window_resize=False)
            return

        if self._active_screen is not None:
            self._disconnect_screen_signals(self._active_screen)

        self._active_screen = next_screen
        if self._active_screen is not None:
            self._connect_screen_signals(self._active_screen)

        self._recalculate_and_apply_scale(force_window_resize=False)

    def _connect_screen_signals(self, screen: QScreen) -> None:
        screen.logicalDotsPerInchChanged.connect(self._on_screen_metric_event)
        screen.geometryChanged.connect(self._on_screen_metric_event)
        screen.availableGeometryChanged.connect(self._on_screen_metric_event)

    def _disconnect_screen_signals(self, screen: QScreen) -> None:
        for signal in (
            screen.logicalDotsPerInchChanged,
            screen.geometryChanged,
            screen.availableGeometryChanged,
        ):
            try:
                signal.disconnect(self._on_screen_metric_event)
            except (RuntimeError, TypeError):
                pass

    def _on_screen_metric_event(self, *_args: object) -> None:
        self._recalculate_and_apply_scale(force_window_resize=False)

    def _on_app_screen_event(self, *_args: object) -> None:
        self._on_window_screen_changed(self._current_screen())

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self._initialize_screen_tracking()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._post_worker and self._post_worker.isRunning():
            self._post_worker.wait(3000)
        if self._verify_worker and self._verify_worker.isRunning():
            self._verify_worker.wait(3000)

        if self._active_screen is not None:
            self._disconnect_screen_signals(self._active_screen)
            self._active_screen = None

        self._save_ui_to_settings()
        self._settings_service.save(self._settings)
        self._append_log(self._logger.info("Приложение закрыто."))
        self._logger.flush()
        super().closeEvent(event)
