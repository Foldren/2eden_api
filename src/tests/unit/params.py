from pytest import param
from starlette.status import (HTTP_409_CONFLICT, HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_202_ACCEPTED,
                              HTTP_208_ALREADY_REPORTED, HTTP_201_CREATED, HTTP_401_UNAUTHORIZED)
from conftest import init_data

register_params = (
    param({"chat_id": 1, "token": "1", "country": "ru"}, "no_referral_code", HTTP_201_CREATED,
          id="without_referral_code"),
    param({"chat_id": 2, "token": "2", "country": "ru"}, "referral_code", HTTP_201_CREATED,
          id="with_referral_code"),
    param({"chat_id": 2, "token": "2", "country": "ru"}, "with_register_ci", HTTP_208_ALREADY_REPORTED,
          id="with_register_chat_id"),
)

login_params = (
    param("invalid", HTTP_401_UNAUTHORIZED, id="invalid_init_data"),
    param(init_data, HTTP_200_OK, id="valid_init_data"),
)

update_rank_params = (
    param("without_coins", HTTP_409_CONFLICT, id="without_coins"),
    param("with_coins", HTTP_202_ACCEPTED, id="with_coins"),
    param("with_max_rank", HTTP_409_CONFLICT, id="with_max_rank"),
)

start_mining_params = (
    param("with_small_rank", HTTP_409_CONFLICT, id="with_small_rank"),
    param("without_constraints", HTTP_202_ACCEPTED, id="without_constraints"),
    param("with_active_mining", HTTP_409_CONFLICT, id="with_active_mining"),
    param("with_reward", HTTP_409_CONFLICT, id="with_reward"),
)

end_mining_params = (
    param("without_constraints", HTTP_202_ACCEPTED, id="without_constraints"),
    param("with_small_rank", HTTP_409_CONFLICT, id="with_small_rank"),
    param("with_not_end_mining", HTTP_409_CONFLICT, id="with_not_end_mining"),
    param("with_not_active_mining", HTTP_409_CONFLICT, id="with_not_active_mining"),
)

get_reward_list_params = (
    param("with_rewards", HTTP_200_OK, id="with_rewards"),
    param("without_rewards", HTTP_404_NOT_FOUND, id="without_rewards"),
)

get_reward_params = (
    param("without_rewards", HTTP_404_NOT_FOUND, id="without_rewards"),
    param("with_someone_else_reward", HTTP_404_NOT_FOUND, id="with_someone_else_reward"),
    param("with_own_reward", HTTP_200_OK, id="with_own_reward"),
)

sync_clicks_params = (
    param("with_energy", HTTP_200_OK, id="with_energy"),
    param("without_energy", HTTP_409_CONFLICT, id="without_energy"),
)

inspiration_params = (
    param("with_small_rank", HTTP_409_CONFLICT, id="with_small_rank"),
    param("without_boosts", HTTP_409_CONFLICT, id="without_boosts"),
    param("without_constraints", HTTP_200_OK, id="without_constraints"),
    param("with_active_boost", HTTP_409_CONFLICT, id="with_active_boost"),
)

replenishment_params = (
    param("with_small_rank", HTTP_409_CONFLICT, id="with_small_rank"),
    param("without_boosts", HTTP_409_CONFLICT, id="without_boosts"),
    param("with_max_energy", HTTP_409_CONFLICT, id="with_max_energy"),
    param("without_constraints", HTTP_200_OK, id="without_constraints"),
)
