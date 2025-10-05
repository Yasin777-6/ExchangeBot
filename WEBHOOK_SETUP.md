# 🔗 Webhook Setup Guide

## Что такое Webhook?

Вместо того, чтобы бот постоянно спрашивал Telegram "есть ли новые сообщения?" (polling), 
Telegram сам отправляет обновления на ваш сервер (webhook). Это эффективнее для production.

---

## 🚀 Быстрая настройка

### 1. Убедитесь, что приложение развернуто

Ваш сайт должен быть доступен по HTTPS (Railway автоматически предоставляет HTTPS).

### 2. Установите webhook

#### Вариант A: Автоматически через Django

Откройте в браузере:
```
https://exchangebot-production-8f2a.up.railway.app/bot/set-webhook/
```

Вы увидите:
```json
{
  "ok": true,
  "webhook_url": "https://exchangebot-production-8f2a.up.railway.app/bot/webhook/",
  "message": "Webhook установлен успешно!"
}
```

#### Вариант B: Через management команду

```bash
python manage.py setup_webhook --url https://exchangebot-production-8f2a.up.railway.app/bot/webhook/
```

#### Вариант C: Добавить в Procfile (уже добавлено!)

```
release: python manage.py migrate && python manage.py setup_webhook --url https://exchangebot-production-8f2a.up.railway.app/bot/webhook/
```

### 3. Проверьте статус webhook

Откройте в браузере:
```
https://exchangebot-production-8f2a.up.railway.app/bot/webhook-info/
```

Или через команду:
```bash
python manage.py setup_webhook --info
```

---

## 📊 Управление Webhook

### Проверить информацию
```bash
python manage.py setup_webhook --info
```

Или откройте:
```
https://your-app.railway.app/bot/webhook-info/
```

### Установить webhook
```bash
python manage.py setup_webhook --url https://your-app.railway.app/bot/webhook/
```

### Удалить webhook
```bash
python manage.py setup_webhook --delete
```

Или откройте:
```
https://your-app.railway.app/bot/delete-webhook/
```

---

## 🔧 Troubleshooting

### Webhook не работает

1. **Проверьте URL**
   ```bash
   python manage.py setup_webhook --info
   ```
   
   URL должен быть: `https://your-app.railway.app/bot/webhook/`

2. **Проверьте HTTPS**
   - Telegram требует HTTPS для webhook
   - Railway автоматически предоставляет HTTPS

3. **Проверьте логи**
   ```bash
   railway logs
   ```

4. **Проверьте CSRF settings**
   - Убедитесь, что ваш домен в `CSRF_TRUSTED_ORIGINS`
   - Проверьте `@csrf_exempt` на webhook view

### Ошибка "Conflict: terminated by other getUpdates"

Это значит, что бот все еще работает в режиме polling. 

**Решение:**
1. Удалите webhook:
   ```bash
   python manage.py setup_webhook --delete
   ```
2. Остановите все экземпляры бота
3. Установите webhook заново

### Бот не отвечает

1. Проверьте, что webhook установлен:
   ```bash
   python manage.py setup_webhook --info
   ```

2. Проверьте логи Railway:
   ```bash
   railway logs
   ```

3. Проверьте, что Django app запущен:
   ```bash
   curl https://your-app.railway.app/bot/webhook/
   ```

---

## 🔄 Переключение между Polling и Webhook

### Из Polling в Webhook:

1. Остановите бот (если запущен):
   ```bash
   # Ctrl+C или остановить процесс
   ```

2. Установите webhook:
   ```bash
   python manage.py setup_webhook --url https://your-app.railway.app/bot/webhook/
   ```

3. Убедитесь, что в Procfile только:
   ```
   web: gunicorn exchange.wsgi --log-file -
   ```

### Из Webhook в Polling:

1. Удалите webhook:
   ```bash
   python manage.py setup_webhook --delete
   ```

2. Запустите бот:
   ```bash
   python manage.py run_bot
   ```

---

## 📝 Endpoints

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/bot/webhook/` | POST | Принимает обновления от Telegram |
| `/bot/set-webhook/` | GET/POST | Установить webhook |
| `/bot/delete-webhook/` | GET/POST | Удалить webhook |
| `/bot/webhook-info/` | GET | Информация о webhook |

---

## ✅ Railway Deployment Checklist

- [ ] Приложение развернуто на Railway
- [ ] HTTPS доступен (автоматически на Railway)
- [ ] Webhook URL установлен
- [ ] CSRF_TRUSTED_ORIGINS включает домен Railway
- [ ] Procfile содержит только `web` процесс (НЕ `bot`)
- [ ] Бот отвечает на `/start`

---

## 🎉 Готово!

Теперь ваш бот работает через webhook! 

**Преимущества:**
- ✅ Моментальные ответы (нет задержки polling)
- ✅ Меньше нагрузки на сервер
- ✅ Один процесс вместо двух
- ✅ Лучше для Railway/Heroku

**Проверьте:**
1. Откройте бота в Telegram
2. Отправьте `/start`
3. Бот должен ответить мгновенно!
