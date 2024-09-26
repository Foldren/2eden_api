## Приложение масштабируется по следующим правилам:
* Сгенерировать файл pgtune_init по ссылке, с необходимыми
опциями системы.
* pgtune_init.sql -> max_connections: Учитывать что max_connections в postgresql = CPUs (потоки) * 4
* config.py -> TORTOISE_CONFIG: Учитывать что maxsize в asyncpg Tortoise orm = max_connections / 10
* app.py -> uvicorn: Учитывать число воркеров, 5 для ~500RPS

_Для текущей настройки используется ~13 потоков | 6 ядер 4ГГц, 
результат ~500RPS+._

