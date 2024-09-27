from datetime import timedelta, datetime
from aiogram.utils.web_app import safe_parse_webapp_init_data, WebAppInitData
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from httpx import Response
from pytz import timezone
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND
from config import TOKEN
from models import User, Reward, Task, RankVisibility, RewardType, VisibilityType
from better_profanity import profanity
from spellchecker import SpellChecker


async def get_daily_reward(user: User) -> None:
    """
    Функция для получения награды за серию авторизаций в игре.
    :param user: User авторизовавшегося юзера с "activity"
    """
    dt_after_get_rw = datetime.fromisoformat(user.activity.last_daily_reward.isoformat()).replace(tzinfo=timezone("Europe/Moscow"))
    dt_last_login = datetime.fromisoformat(user.activity.last_login_date.isoformat()).replace(tzinfo=timezone("Europe/Moscow"))

    time_d_after_get_reward = datetime.now(tz=timezone("Europe/Moscow")) - dt_after_get_rw
    time_d_after_last_login = datetime.now(tz=timezone("Europe/Moscow")) - dt_last_login

    if timedelta(days=2) > time_d_after_get_reward > timedelta(days=1):
        user.activity.active_days += 1
        user.activity.last_daily_reward = datetime.now(tz=timezone("Europe/Moscow"))

        match user.activity.active_days:
            case 1:
                await Reward.create(type=RewardType.LAUNCHES_SERIES, user_id=user.id, amount=500)
            case 2:
                await Reward.create(type=RewardType.LAUNCHES_SERIES, user_id=user.id, amount=1000)
            case 3:
                await Reward.create(type=RewardType.LAUNCHES_SERIES, user_id=user.id, amount=1000,
                                    inspirations=1)
            case 4:
                await Reward.create(type=RewardType.LAUNCHES_SERIES, user_id=user.id, amount=1000,
                                    inspirations=1, replenishments=1)
            case 5:
                await Reward.create(type=RewardType.LAUNCHES_SERIES, user_id=user.id, amount=1000,
                                    inspirations=2, replenishments=1)
            case 6:
                await Reward.create(type=RewardType.LAUNCHES_SERIES, user_id=user.id, amount=5000,
                                    inspirations=2, replenishments=2)
            case 7:
                await Reward.create(type=RewardType.LAUNCHES_SERIES, user_id=user.id, amount=10000,
                                    inspirations=2, replenishments=2)
            case _:
                await Reward.create(type=RewardType.LAUNCHES_SERIES, user_id=user.id, amount=10000,
                                    inspirations=2, replenishments=2)

    elif timedelta(days=2) <= time_d_after_last_login:
        user.activity.active_days = 0
        user.activity.last_daily_reward = datetime.now(tz=timezone("Europe/Moscow"))

    user.activity.last_login_date = datetime.now(tz=timezone("Europe/Moscow"))
    await user.activity.save()


async def get_referral_reward(lead: User, referral_code: str) -> None:
    """
    Функция для получения награды за зарегистрированного реферала.
    :param lead: объект модели User лида
    :param referral_code: код из реферальной ссылки
    """
    referrer = await User.filter(referral_code=referral_code).select_related("stats").first()
    if referrer:
        lead.referrer_id = referrer.id
        await lead.save()

        referrer.stats.invited_friends += 1
        await referrer.stats.save()

        match referrer.stats.invited_friends:
            case 1:
                await Reward.create(type=RewardType.INVITE_FRIENDS, user_id=referrer.id, amount=2000)
            case 5:
                await Reward.create(type=RewardType.INVITE_FRIENDS, user_id=referrer.id, amount=5000)
            case 100:
                await Reward.create(type=RewardType.INVITE_FRIENDS, user_id=referrer.id, amount=50000)
            case 1000:
                await Reward.create(type=RewardType.INVITE_FRIENDS, user_id=referrer.id, amount=250000)


async def send_referral_mining_reward(extraction: int, referrer_id: int = None) -> None:
    """
    Отправка процентов с добычи по майнингу реферреру.
    :param referrer_id: айди реферрера
    :param extraction: добыча с майнинга реферала
    """

    # Если нет реферрера то не выполняем
    print("mining refererer id" + str(referrer_id))
    if referrer_id is None:
        return

    referrer_rw = await Reward.filter(user_id=referrer_id, type=RewardType.MINING_REFERRAL).first()
    income_5_perc = int(extraction * 0.05)

    if referrer_rw is not None:
        referrer_rw.amount += income_5_perc
        await referrer_rw.save()
    else:
        await Reward.create(user_id=referrer_id, type=RewardType.MINING_REFERRAL, amount=income_5_perc)

    referrer_upper = await User.filter(id=referrer_id).first()
    referrer_upper_id = referrer_upper.referrer_id

    # Если у реферрера нет реферрера то не выполняем
    if referrer_upper_id is None:
        return

    referrer_upper_rw = await Reward.filter(user_id=referrer_upper_id, type=RewardType.MINING_REFERRAL).first()
    income_1_perc = int(extraction * 0.01)

    if referrer_upper_rw is not None:
        referrer_upper_rw.amount += income_1_perc
        await referrer_upper_rw.save()
    else:
        await Reward.create(user_id=referrer_upper_id, type=RewardType.MINING_REFERRAL, amount=income_1_perc)


async def sync_energy(user: User) -> None:
    """
    Функция для синхронизации энергии. Обновляет дату синхронизации и меняет кол-во энергии.
    :param user: объект модели User с включенными: activity, stats, rank
    """
    dt_last_sync_energy = datetime.fromisoformat(user.activity.last_sync_energy.isoformat())
    secs_from_last_sync = (datetime.now(tz=timezone("Europe/Moscow")) - dt_last_sync_energy).seconds

    accumulated_energy = max(secs_from_last_sync, 1) * user.rank.energy_per_sec
    user.stats.energy += accumulated_energy

    if user.stats.energy > user.rank.max_energy:
        user.stats.energy = user.rank.max_energy

    user.activity.last_sync_energy = datetime.now(tz=timezone("Europe/Moscow"))

    await user.stats.save()
    await user.activity.save()


async def check_task_visibility(task: Task, user: User):
    if task.visibility.type == VisibilityType.RANK:
        rank_visibility = await RankVisibility.get(visibility=task.visibility)
        return user.rank.league >= rank_visibility.rank.league

    elif task.visibility.type == VisibilityType.ALLWAYS:
        return True

    return False


async def assert_status_code(response: Response, status_code: int) -> None:
    """
    Функция для быстрой генерации assert по status code, для тестов.
    :param response: httpx.Response
    :param status_code: Starlette.status
    """
    frmt_text = f"[Message: {response.json()["message"]["text"]}]"
    assert response.status_code == status_code, frmt_text
    print(frmt_text)  # Это нужный вывод


async def validate_telegram_hash(
        x_telegram_init_data: str = Security(APIKeyHeader(name="X-Telegram-Init-Data"))) -> WebAppInitData:
    """
    Fastapi Depend для валидации telegram hash юзера, возвращает init_data, если все окей.
    :param x_telegram_init_data: заголовок с window.Telegram.WebApp.initData
    :return:
    """
    # Валидируем init data tg юзера
    try:
        init_data = safe_parse_webapp_init_data(token=TOKEN, init_data=x_telegram_init_data)
        user = await User.filter(id=init_data.user.id).first()

        if user:
            return init_data
        else:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Для начала работы нажмите /start.")

    except ValueError:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Данные юзера Telegram не валидны.")


async def ai_msg_base_check(question: str) -> None:
    """
    Функция для базовых проверок вопроса на английском (длина, корректность ввода, мат).
    :param question: вопрос, заданный юзером через бот
    """
    profanity.load_censor_words(whitelist_words=["god"])  # подгружаем список нецензурных слов
    spell = SpellChecker(language='en')  # спелл объект для проверки орфографии
    corrects_words = [spell.correction(word) for word in question.split()]  # список автооткорректированных слов

    assert None not in corrects_words, "❓ Я не могу прочесть твое заклинание, послушник мой."
    assert len(question) >= 10, "🌀 Слишком короткое сообщение, аколит."
    assert len(question.split()) >= 2, "👁‍🗨 Слишком мало слов в сообщении, аколит."
    assert "*" not in profanity.censor(question), "💢 Послушник мой, нельзя использовать мат в заклинаниях!"
