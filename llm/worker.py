from PySide6.QtCore import QThread, Signal

from core.messages import EmotionEvent, LLMTextEvent
from core.stream_parser import LLMStreamParser


class LLMWorker(QThread):
    token_signal = Signal(str)
    emotion_signal = Signal(str)
    finished_signal = Signal()
    error_signal = Signal(str)

    def __init__(self, manager, user_input: str) -> None:
        super().__init__()
        self.manager = manager
        self.user_input = user_input
        self.stream_parser = LLMStreamParser()

    def run(self) -> None:
        try:
            for token in self.manager.chat_stream(self.user_input):
                self._dispatch_events(self.stream_parser.feed(token))

            self._dispatch_events(self.stream_parser.flush())
            self.finished_signal.emit()
        except Exception as exc:
            self.error_signal.emit(str(exc))

    def _dispatch_events(self, events) -> None:
        for event in events:
            if isinstance(event, EmotionEvent):
                self.emotion_signal.emit(event.emotion)
            elif isinstance(event, LLMTextEvent):
                self.token_signal.emit(event.text)
