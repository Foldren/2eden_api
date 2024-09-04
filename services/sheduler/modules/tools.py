from typing import Any


async def gen_ai_quests_list(l_chat_id: list[int],
                             questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"question": question, "acolyte_id": chat_id} for chat_id, question in zip(l_chat_id, questions)]
