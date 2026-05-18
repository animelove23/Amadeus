from core.messages import EmotionEvent
from core.stream_parser import LLMStreamParser


def _parse_emotion(emotion: str) -> str:
    parser = LLMStreamParser()
    events = parser.feed(f"[emotion={emotion}]\nHello") + parser.flush()
    emotion_events = [event for event in events if isinstance(event, EmotionEvent)]
    return emotion_events[0].emotion


def test_stream_parser_accepts_new_emotions() -> None:
    assert _parse_emotion("playful") == "playful"
    assert _parse_emotion("shy") == "shy"


def test_stream_parser_falls_back_to_neutral_for_unknown_emotions() -> None:
    assert _parse_emotion("unknown") == "neutral"
