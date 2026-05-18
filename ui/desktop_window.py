from __future__ import annotations

from collections import deque
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from llm.worker import LLMWorker


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class SceneBackground(QWidget):
    """用绘制而不是业务逻辑营造视觉小说的舞台感。"""

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt naming convention
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()

        sky = QLinearGradient(0, 0, 0, rect.height())
        sky.setColorAt(0.0, QColor("#1b2433"))
        sky.setColorAt(0.48, QColor("#314358"))
        sky.setColorAt(1.0, QColor("#0f141c"))
        painter.fillRect(rect, sky)

        # 远景光斑：让画面不像普通深色窗口，而像一张待机 CG。
        glow = QLinearGradient(0, 0, rect.width(), rect.height())
        glow.setColorAt(0.0, QColor(157, 195, 224, 65))
        glow.setColorAt(0.55, QColor(65, 87, 118, 20))
        glow.setColorAt(1.0, QColor(13, 18, 26, 0))
        painter.fillRect(rect, glow)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 18))
        painter.drawEllipse(rect.width() - 360, 48, 250, 250)
        painter.setBrush(QColor(255, 255, 255, 10))
        painter.drawEllipse(rect.width() - 520, 120, 320, 320)

        # 简化后的“实验室”剪影，只提供层次，不抢对白。
        painter.setBrush(QColor(10, 15, 22, 95))
        painter.drawRect(0, int(rect.height() * 0.60), rect.width(), rect.height())
        painter.setBrush(QColor(12, 18, 26, 72))
        painter.drawRect(32, 92, 132, int(rect.height() * 0.43))
        painter.drawRect(188, 122, 110, int(rect.height() * 0.39))
        painter.drawRect(rect.width() - 270, 102, 180, int(rect.height() * 0.41))

        painter.setPen(QPen(QColor(255, 255, 255, 22), 1))
        for y in range(0, rect.height(), 4):
            painter.drawLine(0, y, rect.width(), y)

        vignette = QLinearGradient(0, 0, 0, rect.height())
        vignette.setColorAt(0.0, QColor(0, 0, 0, 70))
        vignette.setColorAt(0.18, QColor(0, 0, 0, 0))
        vignette.setColorAt(0.80, QColor(0, 0, 0, 25))
        vignette.setColorAt(1.0, QColor(0, 0, 0, 125))
        painter.fillRect(rect, vignette)


class DesktopChatWindow(QWidget):
    """Galgame 风格桌面窗口：UI 只消费事件，不掺入 LLM / RAG / Agent 逻辑。"""

    CHARACTER_NAME = "牧濑红莉栖"

    def __init__(self, manager) -> None:
        super().__init__()

        self.manager = manager
        self.worker: LLMWorker | None = None
        self.current_ai_text = ""
        self.current_speaker = self.CHARACTER_NAME
        self.transcript: deque[str] = deque(maxlen=80)
        self.sprite_paths = {
            "neutral": PROJECT_ROOT / "assets" / "kurisu" / "neutral.jpg",
            "happy": PROJECT_ROOT / "assets" / "kurisu" / "happy.jpg",
            "angry": PROJECT_ROOT / "assets" / "kurisu" / "angry.jpg",
            "playful": PROJECT_ROOT / "assets" / "kurisu" / "playful.jpg",
            "shy": PROJECT_ROOT / "assets" / "kurisu" / "shy.jpg",
        }
        self.current_emotion = "neutral"

        self.setWindowTitle("Amadeus")
        self.resize(1100, 700)
        self.setMinimumSize(900, 560)
        self.setStyleSheet(self._build_stylesheet())

        self.background = SceneBackground()
        self.overlay = QWidget()
        self.overlay.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._build_hud()
        self._build_stage()
        self._build_dialogue_panel()
        self._build_layout()

        self.send_button.clicked.connect(self.send_message)
        self.input_box.returnPressed.connect(self.send_message)
        self.log_button.clicked.connect(self.toggle_log)

        self.set_sprite("neutral")
        self._show_dialogue(
            self.CHARACTER_NAME,
            "……系统已就绪。你可以开始说话。",
        )

    def _build_hud(self) -> None:
        self.date_label = QLabel("07 / 28\nWED")
        self.date_label.setObjectName("dateLabel")
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.mode_label = QLabel("AMADEUS // ONLINE")
        self.mode_label.setObjectName("modeLabel")
        self.mode_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def _build_stage(self) -> None:
        self.sprite_card = QFrame()
        self.sprite_card.setObjectName("spriteCard")
        self.sprite_card.setFixedWidth(420)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 120))
        self.sprite_card.setGraphicsEffect(shadow)

        sprite_layout = QVBoxLayout(self.sprite_card)
        sprite_layout.setContentsMargins(10, 10, 10, 10)

        self.sprite_label = QLabel()
        self.sprite_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sprite_label.setMinimumHeight(400)
        sprite_layout.addWidget(self.sprite_label)

        self.log_panel = QTextEdit()
        self.log_panel.setObjectName("logPanel")
        self.log_panel.setReadOnly(True)
        self.log_panel.setVisible(False)
        self.log_panel.setFixedWidth(320)

    def _build_dialogue_panel(self) -> None:
        self.dialogue_frame = QFrame()
        self.dialogue_frame.setObjectName("dialogueFrame")
        self.dialogue_frame.setFixedHeight(250)

        dialogue_layout = QVBoxLayout(self.dialogue_frame)
        dialogue_layout.setContentsMargins(30, 22, 30, 18)
        dialogue_layout.setSpacing(12)

        self.dialogue_text = QTextEdit()
        self.dialogue_text.setObjectName("dialogueText")
        self.dialogue_text.setReadOnly(True)
        self.dialogue_text.setFrameShape(QFrame.Shape.NoFrame)
        self.dialogue_text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.dialogue_text.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.dialogue_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.dialogue_text.setFixedHeight(92)

        name_row = QHBoxLayout()
        name_row.setSpacing(12)

        left_rule = QFrame()
        left_rule.setObjectName("nameRule")
        left_rule.setFrameShape(QFrame.Shape.HLine)

        self.name_label = QLabel(self.CHARACTER_NAME)
        self.name_label.setObjectName("nameLabel")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        right_rule = QFrame()
        right_rule.setObjectName("nameRule")
        right_rule.setFrameShape(QFrame.Shape.HLine)

        name_row.addStretch(1)
        name_row.addWidget(left_rule, 1)
        name_row.addWidget(self.name_label)
        name_row.addWidget(right_rule, 1)
        name_row.addStretch(1)

        input_row = QHBoxLayout()
        input_row.setSpacing(10)

        self.input_box = QLineEdit()
        self.input_box.setObjectName("inputBox")
        self.input_box.setPlaceholderText("输入你的台词……")

        self.send_button = QPushButton("发送")
        self.send_button.setObjectName("sendButton")

        input_row.addWidget(self.input_box, 1)
        input_row.addWidget(self.send_button)

        controls_row = QHBoxLayout()
        controls_row.setSpacing(8)

        self.auto_badge = QLabel("F3  AUTO")
        self.auto_badge.setObjectName("shortcutBadge")

        self.skip_badge = QLabel("E  SKIP")
        self.skip_badge.setObjectName("shortcutBadge")

        self.log_button = QPushButton("L  LOG")
        self.log_button.setObjectName("logButton")

        self.emotion_label = QLabel("MOOD // NEUTRAL")
        self.emotion_label.setObjectName("emotionLabel")

        controls_row.addWidget(self.auto_badge)
        controls_row.addWidget(self.skip_badge)
        controls_row.addWidget(self.log_button)
        controls_row.addStretch(1)
        controls_row.addWidget(self.emotion_label)

        dialogue_layout.addWidget(self.dialogue_text)
        dialogue_layout.addLayout(name_row)
        dialogue_layout.addLayout(input_row)
        dialogue_layout.addLayout(controls_row)

    def _build_layout(self) -> None:
        overlay_layout = QVBoxLayout(self.overlay)
        overlay_layout.setContentsMargins(22, 18, 22, 18)
        overlay_layout.setSpacing(16)

        top_row = QHBoxLayout()
        top_row.addWidget(self.date_label)
        top_row.addStretch(1)
        top_row.addWidget(self.mode_label)

        stage_row = QHBoxLayout()
        stage_row.addStretch(1)
        stage_row.addWidget(self.log_panel)
        stage_row.addSpacing(16)
        stage_row.addWidget(self.sprite_card)

        overlay_layout.addLayout(top_row)
        overlay_layout.addLayout(stage_row, 1)
        overlay_layout.addWidget(self.dialogue_frame)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self.background)

        self.background.setLayout(QVBoxLayout())
        self.background.layout().setContentsMargins(0, 0, 0, 0)
        self.background.layout().addWidget(self.overlay)

    def send_message(self) -> None:
        user_input = self.input_box.text().strip()
        if not user_input:
            return

        self.input_box.clear()
        self.current_ai_text = ""
        self.current_speaker = "你"
        self._append_log("你", user_input)
        self._show_dialogue("你", user_input)
        self.mode_label.setText("AMADEUS // THINKING")
        self.send_button.setEnabled(False)
        self.input_box.setEnabled(False)

        self.worker = LLMWorker(manager=self.manager, user_input=user_input)
        self.worker.token_signal.connect(self.on_token)
        self.worker.emotion_signal.connect(self.on_emotion)
        self.worker.error_signal.connect(self.on_error)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

    def on_token(self, token: str) -> None:
        if self.current_speaker != self.CHARACTER_NAME:
            self.current_speaker = self.CHARACTER_NAME
            self.current_ai_text = ""
            self._show_dialogue(self.CHARACTER_NAME, "")

        self.current_ai_text += token
        self.dialogue_text.setPlainText(self.current_ai_text)
        self._scroll_dialogue_to_bottom()

    def on_error(self, error: str) -> None:
        self._append_log("系统", f"错误：{error}")
        self._show_dialogue("系统", f"错误：{error}")
        self.mode_label.setText("AMADEUS // ERROR")
        self.send_button.setEnabled(True)
        self.input_box.setEnabled(True)

    def on_finished(self) -> None:
        if self.current_ai_text:
            self._append_log(self.CHARACTER_NAME, self.current_ai_text)

        self.mode_label.setText("AMADEUS // ONLINE")
        self.send_button.setEnabled(True)
        self.input_box.setEnabled(True)
        self.input_box.setFocus()

    def on_emotion(self, emotion: str) -> None:
        self.set_sprite(emotion)

    def set_sprite(self, emotion: str) -> None:
        self.current_emotion = emotion if emotion in self.sprite_paths else "neutral"
        path = self.sprite_paths[self.current_emotion]
        pixmap = QPixmap(str(path))

        if pixmap.isNull():
            self._append_log("系统", f"警告：找不到立绘 {path}")
            return

        scaled = pixmap.scaled(
            390,
            470,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.sprite_label.setPixmap(scaled)
        self.emotion_label.setText(f"MOOD // {self.current_emotion.upper()}")

    def toggle_log(self) -> None:
        self.log_panel.setVisible(not self.log_panel.isVisible())
        self.log_button.setText("L  CLOSE" if self.log_panel.isVisible() else "L  LOG")

    def _append_log(self, speaker: str, text: str) -> None:
        line = f"{speaker}：{text}"
        self.transcript.append(line)
        self.log_panel.setPlainText("\n\n".join(self.transcript))
        cursor = self.log_panel.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_panel.setTextCursor(cursor)

    def _show_dialogue(self, speaker: str, text: str) -> None:
        self.name_label.setText(speaker)
        self.dialogue_text.setPlainText(text)
        self.dialogue_text.verticalScrollBar().setValue(0)

    def _scroll_dialogue_to_bottom(self) -> None:
        scroll_bar = self.dialogue_text.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())

    def _build_stylesheet(self) -> str:
        return """
        QWidget {
            color: #f7f3ea;
            font-family: "Microsoft YaHei UI", "Noto Sans CJK SC", sans-serif;
        }

        #dateLabel {
            min-width: 132px;
            min-height: 76px;
            background-color: rgba(15, 23, 35, 175);
            border: 1px solid rgba(230, 239, 248, 120);
            color: #f3efe6;
            font-size: 22px;
            font-weight: 600;
            letter-spacing: 2px;
        }

        #modeLabel {
            color: rgba(238, 242, 247, 205);
            font-size: 14px;
            letter-spacing: 2px;
            padding-right: 6px;
        }

        #spriteCard {
            background-color: rgba(245, 247, 250, 28);
            border: 1px solid rgba(255, 255, 255, 80);
        }

        #dialogueFrame {
            background-color: rgba(5, 8, 14, 214);
            border-top: 1px solid rgba(245, 245, 245, 125);
        }

        #dialogueText {
            background-color: transparent;
            border: none;
            color: #fbf8f1;
            font-size: 25px;
            line-height: 1.4;
            padding: 0;
        }

        #dialogueText QScrollBar:vertical {
            width: 8px;
            background: rgba(255, 255, 255, 18);
            margin: 0;
        }

        #dialogueText QScrollBar::handle:vertical {
            background: rgba(243, 239, 230, 150);
            min-height: 24px;
        }

        #dialogueText QScrollBar::add-line:vertical,
        #dialogueText QScrollBar::sub-line:vertical {
            height: 0;
        }

        #nameLabel {
            min-width: 140px;
            color: #f1e7d0;
            font-size: 18px;
            font-weight: 600;
            padding: 2px 14px;
        }

        #nameRule {
            background-color: rgba(255, 255, 255, 110);
            max-height: 1px;
        }

        #inputBox {
            min-height: 40px;
            background-color: rgba(255, 255, 255, 18);
            border: 1px solid rgba(255, 255, 255, 95);
            color: #fffaf2;
            padding: 0 14px;
            font-size: 17px;
        }

        #inputBox:disabled {
            color: rgba(255, 255, 255, 120);
        }

        #sendButton,
        #logButton {
            min-height: 40px;
            background-color: rgba(17, 28, 43, 185);
            border: 1px solid rgba(224, 233, 242, 120);
            color: #f6f0e5;
            padding: 0 16px;
            font-size: 15px;
        }

        #sendButton:hover,
        #logButton:hover {
            background-color: rgba(37, 55, 78, 210);
        }

        #sendButton:disabled {
            color: rgba(255, 255, 255, 120);
            background-color: rgba(17, 28, 43, 110);
        }

        #shortcutBadge {
            background-color: rgba(23, 37, 54, 170);
            border: 1px solid rgba(224, 233, 242, 95);
            color: rgba(246, 240, 229, 215);
            padding: 5px 9px;
            font-size: 13px;
        }

        #emotionLabel {
            color: rgba(246, 240, 229, 210);
            font-size: 13px;
            letter-spacing: 1px;
        }

        #logPanel {
            background-color: rgba(8, 12, 20, 215);
            border: 1px solid rgba(255, 255, 255, 95);
            color: #f8f4ec;
            font-size: 15px;
            padding: 12px;
        }
        """
