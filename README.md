# Проектная работа 10 спринта

# Описание
Данный сервис представляет собой функционал создания и отправки уведомлений.

Используемые библиотеки

Версия python 3.10

- ORM: `SQLAlchemy`
- http: `FastAPI`
- БД: `Postgres`
- Брокер сообщений: `RabbitMQ`
- Очередь: `Celery`
- валидация: `Pydantic`
- документация: `Swagger`


# Ошибки и HTTP статусы

Для обозначения внештатных ситуаций сервиса используются HTTP статусы. В целом, следующая спецификация
соответствует HTTP спецификации, просто здесь присутствует некоторая поправка на то, что это RESTlike сервис.

- `200` Штатный код для успешной операции
- `201` Сущность создана (`POST` запросы с созданием нового элемента)
- `400` Ошибка бизнес логики (всё что связано с конкретной логикой сущности)
- `401` Ошибка авторизации (пользователь не авторизован, токен истёк)
- `404` Объект не найден в базе данных
- `409` Проблема уникальности (подобная сущность уже существует)
- `422` Ошибка валидации
- `403` Нет прав (у пользователя недостаточно прав в системе)
- `500` Внутренняя ошибка сервиса (**вручную не кидать**)
- `410` Срок действия доступа к ресурсу истёк. (Например, какой-нибудь системный токен)