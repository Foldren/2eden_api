from datetime import timedelta, datetime
from pytz import timezone
from components import enums
from models import User, Reward


async def get_daily_reward(user_id: str):
    user = await User.filter(id=user_id).select_related("activity", "rank", "rewards").first()
    time_d_after_get_reward = datetime.now(tz=timezone("Europe/Moscow")) - user.activity.last_get_daily_reward_date
    time_d_after_login = datetime.now(tz=timezone("Europe/Moscow")) - user.activity.last_login_date

    if (user.activity.last_get_daily_reward_date is None) or (timedelta(days=2) > time_d_after_get_reward > timedelta(days=1)):
        user.activity.active_days += 1
        user.activity.last_get_daily_reward_date = datetime.now(tz=timezone("Europe/Moscow"))

        match user.activity.active_days:
            case 1:
                await Reward.create(type_name=enums.RewardTypeName.invite_friends, user_id=user_id, amount=500)
            case 2:
                await Reward.create(type_name=enums.RewardTypeName.invite_friends, user_id=user_id, amount=1000)
            case 3:
                await Reward.create(type_name=enums.RewardTypeName.invite_friends, user_id=user_id, amount=1000,
                                    inspirations=1)
            case 4:
                await Reward.create(type_name=enums.RewardTypeName.invite_friends, user_id=user_id, amount=1000,
                                    inspirations=1, replenishments=1)
            case 5:
                await Reward.create(type_name=enums.RewardTypeName.invite_friends, user_id=user_id, amount=1000,
                                    inspirations=2, replenishments=1)
            case 6:
                await Reward.create(type_name=enums.RewardTypeName.invite_friends, user_id=user_id, amount=5000,
                                    inspirations=2, replenishments=2)
            case 7:
                await Reward.create(type_name=enums.RewardTypeName.invite_friends, user_id=user_id, amount=10000,
                                    inspirations=2, replenishments=2)
            case _:
                await Reward.create(type_name=enums.RewardTypeName.invite_friends, user_id=user_id, amount=10000,
                                    inspirations=2, replenishments=2)

    if timedelta(days=2) <= time_d_after_login:
        user.activity.active_days = 0
        user.activity.last_get_daily_reward_date = datetime.now(tz=timezone("Europe/Moscow"))

    user.activity.last_login_date = datetime.now(tz=timezone("Europe/Moscow"))
    await user.activity.save()


