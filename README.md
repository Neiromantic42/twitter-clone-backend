# Twitter Clone Backend

Это серверная часть проекта микроблога, реализованная на Python с использованием FastAPI.

## 📦 Функциональность

- Авторизация пользователей реализовано чрез api-key
- Создание, удаление и просмотр твитов
- Загрузка медиа
- Подписки на других пользователей (читать)
- Отписка от пользователей (перестать читать)
- Получение ленты твитов от подписок
- Поставить лайк твиту
- Убрать лайк с твита
- Асинхронная работа с БД PostgreSQL через SQLAlchemy
- Проведение валидации через Pydantic и WTForms

## 🚀 Технологии

- Python 3.11
- FastAPI
- PostgreSQL
- SQLAlchemy (Async)
- Alembic
- Docker
- Pytest
- Uvicorn
- WTForms
- Logging
- Pydantic
- aiofiles (для загрузки медиа)
- Линтеры: `black`, `isort`, `mypy`

## ⚙️ Установка и запуск

1. Клонируйте репозиторий и перейдите в корень проекта:
   ```bash
   git clone https://github.com/Neiromantic42/twitter-clone-backend
   cd twitter_clone_backend
   ```

2. Создайте и активируйте виртуальное окружение:
   ```bash
    python -m venv .venv
    source .venv/bin/activate
   ```

3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

4. Поднимите контейнеры (это и запустит нашу программу) что является педпочтительным способом запуска сервиса:
   ```bash
   docker-compose up -d
   ```

5. API будет доступно по адресу:
   ```bash
   http://localhost:8000
   ```
   
   
## 📁 Структура проекта
.
├── alembic.ini                   # Конфигурация для Alembic (миграции БД)
├── docker-compose.yml            # Docker Compose конфигурация
├── Dockerfile                    # Docker сборка приложения
├── LICENSE                       # Лицензия
├── media/                        # Каталог для загружаемых файлов
├── migrations/                   # Миграции базы данных
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── pyproject.toml                # Настройки проекта (Poetry)
├── pytest.ini                    # Конфигурация Pytest
├── README.md
├── requirements.txt              # Зависимости проекта
├── app/                          # Основная логика приложения
│   ├── main.py                   # Точка входа
│   ├── config.py                 # Конфиги
│   ├── database.py               # Подключение к БД
│   ├── dependencies.py
│   ├── run.py                    # Альтернативный запуск
│   ├── models.py                 # SQLAlchemy модели
│   ├── media/                    # Статика
│   ├── schemas/                  # Pydantic схемы
│   └── templates/                # HTML-шаблоны (Jinja2)
└── tests/                        # Тесты
    ├── conftest.py
    ├── test_*.py
    └── test_media_files/


### 🛠️ Линтинг и статический анализ

В проекте используются следующие инструменты для проверки качества кода:

- 🐍 **mypy** — статическая типизация  
- 🎨 **black** — автоформатирование кода  
- 📚 **isort** — сортировка импортов

#### 🚀 Запуск линтеров

```bash
mypy .
black .
isort .
```

### 🔧 Переменные окружения, используемые в проекте:

```bash
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin
POSTGRES_DB=admin
DATABASE_URL=postgresql+asyncpg://admin:admin@db:5432/admin
```

### 📌 Примечания
   При первом запуске дождитесь, пока база данных станет доступна 
   — используется depends_on и healthcheck в docker-compose.yml.
   Миграции можно выполнять вручную через команду:
```bash
docker-compose exec backend alembic upgrade head
```
### Документация API (Swagger):

Документация доступна при запуске сервиса по адресу:  
[http://localhost:8000/docs](http://localhost:8000/docs)


### 🧪 Тестирование и покрытие кода
Для запуска тестов в контейнере используйте команду:
```bash
docker-compose exec backend pytest --disable-warnings --maxfail=1
```
Если хотите запустить тесты локально, то выполните:
```bash
pytest --disable-warnings --maxfail=1
```
Для генерации отчёта о покрытии кода тестами используется плагин pytest-cov,
в данном случае покрытие тестами обеспечено на 70 процентов. 
Запустите команду:
```bash
pytest --cov=app --cov-report=term-missing
```