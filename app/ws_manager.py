from collections import defaultdict
from fastapi import WebSocket


class ConnectionManager:
    """Хранит активные WebSocket-подключения, сгруппированные по чатам."""

    def __init__(self) -> None:
        # chat_id -> множество активных сокетов
        self.active: dict[int, set[WebSocket]] = defaultdict(set)

    async def connect(self, chat_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active[chat_id].add(websocket)

    def disconnect(self, chat_id: int, websocket: WebSocket) -> None:
        self.active[chat_id].discard(websocket)
        if not self.active[chat_id]:
            self.active.pop(chat_id, None)

    async def broadcast(self, chat_id: int, message: dict) -> None:
        """Рассылает сообщение всем участникам чата, отсеивая мёртвые сокеты."""
        dead: list[WebSocket] = []
        for connection in self.active.get(chat_id, set()):
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for connection in dead:
            self.disconnect(chat_id, connection)


manager = ConnectionManager()
