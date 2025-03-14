Telegram News Bot

Этот Telegram-бот позволяет получать свежие новости из трёх источников и подписываться на ежедневную рассылку. Бот разворачивается на любой машине через Docker.

📌 Возможности

 • Получение новостей из трёх источников:
 
  Kommersant (https://www.kommersant.ru/)
 
  IXBT (https://www.ixbt.com/)
 
  Investing (https://www.investing.com/)
 
 • Подписка на ежедневную рассылку новостей из выбранного источника.
 
 • Отписка от рассылки.
 
 • Гибкая настройка через командный интерфейс.
 
Ссылка на бота в Telegram @resumetestnews_bot

📌Особенности

 • Получение новостей:
Бот собирает и отправляет пользователю последние новости из трёх источников (например, Источник 1, Источник 2 и Источник 3).

 • Подписка и отписка:
Пользователь может подписаться на ежедневную рассылку новостей или отменить подписку, воспользовавшись соответствующими командами.

 • Хранение данных:
Для хранения информации о пользователях и новостях используется база данных PostgreSQL.

 • Контейнеризация:
Приложение разворачивается с помощью Docker, что упрощает установку и масштабирование.

📌Требования

 • Docker:
Для работы требуется установленный Docker.

 • Docker Compose:
Рекомендуется использовать Docker Compose для удобного развёртывания всех контейнеров.

 • Переменные окружения:
Файл .env должен содержать необходимые параметры (например, TELEGRAM_TOKEN, DATABASE_URL и другие настройки).

📌Инструкция по запуску

Для развертывания приложения можно использовать Docker, предварительно создав на машине .env с переменными окружения.

https://hub.docker.com/repositories/lomakomikhail

Так же запуска потребуется сскопировать файл docker-compose.yml на машину и запустить его командой docker-compose up -d. На машине развернется 2 контейнера docker:

1. telegram-bot - сам скрипт бота.
2. postgres_db - база данных с таблицами для работы бота.

DB_PASSWORD язвляется уникальным токеном, не предназначен для общего пользования.

TOKEN является уникальным токеном Telegram бота, не предназначен для общего пользования.
