import re

from core.messages import EmotionEvent, LLMTextEvent, MetadataEvent


class LLMStreamParser:
    """
    解析模型流式输出中的“协议层”和“正文层”。
    当前支持：
        [emotion=happy]
        [voice=kurisu]
    """

    META_LINE_PATTERN = re.compile(r"^\[(?P<name>[A-Za-z_][\w-]*)=(?P<value>[^\]]+)\]$")

    def __init__(self) -> None:
        self.buffer = ""
        self.header_open = True
        self.metadata: dict[str, str] = {}

    def feed(self, chunk: str) -> list[MetadataEvent | EmotionEvent | LLMTextEvent]:
        if not chunk:
            return []

        self.buffer += self._normalize(chunk)
        events: list[MetadataEvent | EmotionEvent | LLMTextEvent] = []

        if self.header_open and self._buffer_is_plain_text():
            self.header_open = False

        events.extend(self._drain_complete_lines())

        if self.header_open and self._buffer_is_plain_text():
            self.header_open = False

        if not self.header_open and self.buffer:
            events.append(LLMTextEvent(self.buffer))
            self.buffer = ""

        return events

    def flush(self) -> list[MetadataEvent | EmotionEvent | LLMTextEvent]:
        if not self.buffer:
            return []

        events: list[MetadataEvent | EmotionEvent | LLMTextEvent] = []

        if self.header_open:
            metadata = self._parse_metadata_line(self.buffer.strip())
            if metadata:
                events.extend(self._build_metadata_events(*metadata))
            else:
                events.append(LLMTextEvent(self.buffer))
        else:
            events.append(LLMTextEvent(self.buffer))

        self.buffer = ""
        self.header_open = False
        return events

    def _drain_complete_lines(self) -> list[MetadataEvent | EmotionEvent | LLMTextEvent]:
        events: list[MetadataEvent | EmotionEvent | LLMTextEvent] = []

        while self.header_open and "\n" in self.buffer:
            line, rest = self.buffer.split("\n", 1)
            stripped_line = line.strip()

            if not stripped_line:
                self.buffer = rest
                continue

            metadata = self._parse_metadata_line(stripped_line)
            if metadata:
                events.extend(self._build_metadata_events(*metadata))
                self.buffer = rest
                continue

            self.header_open = False
            events.append(LLMTextEvent(line + ("\n" if rest else "")))
            self.buffer = rest
            break

        return events

    def _build_metadata_events(self, name: str, value: str) -> list[MetadataEvent | EmotionEvent]:
        self.metadata[name] = value
        events: list[MetadataEvent | EmotionEvent] = [MetadataEvent(name=name, value=value)]

        if name == "emotion":
            events.append(EmotionEvent(emotion=self._normalize_emotion(value)))

        return events

    def _parse_metadata_line(self, line: str) -> tuple[str, str] | None:
        match = self.META_LINE_PATTERN.fullmatch(line)
        if not match:
            return None

        name = match.group("name").strip().lower()
        value = match.group("value").strip()
        return name, value

    def _buffer_is_plain_text(self) -> bool:
        stripped = self.buffer.lstrip()
        if not stripped:
            return False
        return not stripped.startswith("[")

    def _normalize(self, text: str) -> str:
        return text.replace("\r\n", "\n").replace("【", "[").replace("】", "]")

    def _normalize_emotion(self, emotion: str) -> str:
        return emotion if emotion in {"neutral", "happy", "angry"} else "neutral"
