DB_PASSWORD язвляется уникальным токеном, не предназначен для общего пользования.

TOKEN является уникальным токеном Telegram бота, не предназначен для общего пользования.

Ссылка на бота в Telegram @resumetestnews_bot

Для быстрого развертывания приложения можно использовать Docker, предварительно создав на машине .env с переменными окружения.

docker run -d --restart unless-stopped --name telegram-bot --env-file .env lomakomikhail/telegram-bot
