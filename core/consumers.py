import json
from channels.generic.websocket import AsyncWebsocketConsumer

online_users_count = 0


class ChatConsumer(AsyncWebsocketConsumer):
    """Класс для обработки WebSocket-соединений чата и уведомлений"""

    async def connect(self):
        """Обработка подключения клиента, добавление в группу и обновление счетчика"""
        global online_users_count
        self.room_group_name = "global_room"
        self.user = self.scope["user"]

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        online_users_count += 1

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "system_broadcast",
                "count": online_users_count,
                "message": f"Користувач {self.user.username if self.user.is_authenticated else 'Гість'} увійшов до чату.",
            },
        )

    async def disconnect(self, close_code):
        """Обработка отключения клиента, удаление из группы и уменьшение счетчика"""
        global online_users_count

        if online_users_count > 0:
            online_users_count -= 1

        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "system_broadcast",
                "count": online_users_count,
                "message": f"Користувач {self.user.username if self.user.is_authenticated else 'Гість'} вийшов з чату.",
            },
        )

    async def receive(self, text_data):
        """Прием сообщений от клиента, проверка авторизации и маршрутизация по типам событий"""
        data = json.loads(text_data)
        action_type = data.get("type")

        if not self.user.is_authenticated:
            await self.send(
                text_data=json.dumps(
                    {
                        "action": "error_message",
                        "error": "Доступ обмежено! Тільки зареєстровані користувачі можуть надсилати повідомлення.",
                    }
                )
            )
            return

        username = self.user.username

        if action_type == "chat_message":
            message_text = data.get("message")
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_broadcast",
                    "username": username,
                    "message": message_text,
                },
            )

        elif action_type == "push_notification":
            notification_text = data.get("message")
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "push_broadcast",
                    "sender": username,
                    "message": notification_text,
                },
            )

    async def system_broadcast(self, event):
        """Рассылка системных уведомлений (статус онлайна и логи) всем клиентам"""
        await self.send(
            text_data=json.dumps(
                {
                    "action": "update_counter",
                    "count": event["count"],
                    "log": event["message"],
                }
            )
        )

    async def chat_broadcast(self, event):
        """Рассылка новых сообщений чата всем клиентам"""
        await self.send(
            text_data=json.dumps(
                {
                    "action": "new_message",
                    "username": event["username"],
                    "message": event["message"],
                }
            )
        )

    async def push_broadcast(self, event):
        """Рассылка всплывающих push-уведомлений всем клиентам"""
        await self.send(
            text_data=json.dumps(
                {
                    "action": "push_alert",
                    "sender": event["sender"],
                    "message": event["message"],
                }
            )
        )
