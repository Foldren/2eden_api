from deep_translator import GoogleTranslator
from ujson import loads
from components.pydantic_models import Connection
from config import APP_NAME, GPT_SYSTEM_MESSAGES
from modules.logger import Logger


async def get_ai_answers(**kwargs):
    """
    Запускаем таск на получение ответов на вопросы юзеров через OpenAI с проверкой каждые 5 сек.
    """

    conn: Connection = kwargs['conn']  # Redis, OpenAI подключения
    gt: GoogleTranslator = kwargs['gt']  # Google

    try:
        lst_chat_id = await conn.rs.questions.keys()

        # Если нет вопросов ждем 5 секунд и смотрим вопросы снова
        if not lst_chat_id:
            await Logger(APP_NAME).info(msg="Вопросов нет, ожидание 5 секунд.", func_name="get_ai_questions")
            return

        questions = (await conn.rs.questions.json().mget(lst_chat_id, "$"))[0]

        # Формируем ответы через OpenAI
        gpt_quests = [{"question": q['question'], "acolyte_id": c_id} for c_id, q in zip(lst_chat_id, questions)]
        gpt_msgs = GPT_SYSTEM_MESSAGES + ({"role": "system", "content": f"Questions:{gpt_quests}"},)
        gpt_r = await conn.ai_client.chat.completions.create(model="gpt-3.5-turbo",
                                                             messages=gpt_msgs,
                                                             max_tokens=100,
                                                             temperature=1,
                                                             stop=None,
                                                             timeout=30)

        gpt_dict_resp = loads(gpt_r.choices[0].message.content)

        # Формируем список вопросов для загрузки в бд + отправляем ответы пользователям
        loads_new_answ = []
        for qst, answ in zip(questions, gpt_dict_resp):
            ru_answ = gt.translate(answ['answer'])
            loads_new_answ.append({"question": qst['question'], "answer": ru_answ, "embedding": qst['vector']})
            await conn.bot.send_message(chat_id=answ['acolyte_id'], text=ru_answ)

        # Загружаем ответы в db 0
        await conn.rs.index.load(loads_new_answ)
        # Удаляем вопросы из db 14
        await conn.rs.questions.delete(*lst_chat_id)

        await Logger(APP_NAME).success(msg="AI сгенерировал ответы, ожидание вопросов.",
                                       func_name="get_ai_questions")
    except Exception as e:
        await Logger(APP_NAME).error(msg=str(e),
                                     func_name="get_ai_questions")