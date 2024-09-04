from datetime import datetime
from pytz import timezone
from termcolor import colored


class Logger:
    app_name: str
    time_log: datetime
    __prefix_app_param_c: str = colored("app:", 'cyan', force_color=True)
    __prefix_func_param_c: str = colored("func:", 'cyan', force_color=True)

    def __init__(self, app_name=None):
        self.app_name = self.__prefix_app_param_c + app_name
        self.time_log = datetime.now(tz=timezone("Europe/Moscow"))

    async def success(self, msg: str, func_name: str) -> None:
        """
        Метод на получение cообщения типа success.
        :param msg: текст сообщения
        :param func_name: название модуля или функции
        """

        status_operation = colored('success', 'green', force_color=True)
        print(self.time_log, self.app_name, self.__prefix_func_param_c + func_name, f"[{status_operation}]", msg)

    async def info(self, msg: str, func_name: str) -> None:
        """
        Метод на получение cообщения типа info.
        :param msg: текст сообщения
        :param func_name: название модуля или функции
        """

        status_operation = colored('info', 'blue', force_color=True)
        print(self.time_log, self.app_name, self.__prefix_func_param_c + func_name, f"[{status_operation}]", msg)

    async def error(self, msg: str, func_name: str) -> None:
        """
        Метод на получение cообщения типа error.
        :param msg: текст сообщения
        :param func_name: название модуля или функции
        """

        status_operation = colored('info', 'red', force_color=True)
        print(self.time_log, self.app_name, self.__prefix_func_param_c + func_name, f"[{status_operation}]", msg)
