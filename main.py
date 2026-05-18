import sys

from PySide6.QtWidgets import QApplication

from config import LLM_CONFIG
from core.manager import Manager
from llm.adapter import LLMAdapterFactory
from ui.desktop_window import DesktopChatWindow


MODEL_NAME = "deepseek"

config = LLM_CONFIG[MODEL_NAME]

adapter = LLMAdapterFactory.create_adapter(
    provider=config["provider"],
    api_key=config["api_key"],
    base_url=config["base_url"],
    model=config["model"],
)

manager = Manager(
    adapter=adapter,
    system_prompt="""
你正在扮演《命运石之门》中的牧濑红莉栖。
一定要和原文设定和说话语气一致。
你对用户一无所知，只能从上下文中了解。

你每次回复必须使用以下格式：

[emotion=neutral|happy|angry|playful|shy]
正文内容

规则：
1. emotion 只能从 neutral、happy、angry、playful、shy 中选择一个。
2. 普通解释用 neutral。
3. 轻松、认可、开心时用 happy。
4. 吐槽、生气、被冒犯时用 angry。
5. 略带调侃、俏皮时用 playful。
6. 害羞、被夸到不太好意思时用 shy。
7. 正文不要太长。
""",
)

app = QApplication(sys.argv)
window = DesktopChatWindow(manager)
window.show()
sys.exit(app.exec())
