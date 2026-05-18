from dataclasses import dataclass


@dataclass
class UserInputMessage:
    text: str


@dataclass
class LLMTextEvent:
    text: str


@dataclass
class EmotionEvent:
    emotion: str


@dataclass
class MetadataEvent:
    name: str
    value: str


@dataclass
class TTSRequestEvent:
    character: str
    text: str
    emotion: str


@dataclass
class UIOutputEvent:
    text: str
    emotion: str
