from fastapi import WebSocket

from app.core.metrics import WS_CONNECTED_CLIENTS


class WSManager:
    def __init__(self) -> None:
        self.clients: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.clients.append(ws)
        WS_CONNECTED_CLIENTS.set(len(self.clients))

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self.clients:
            self.clients.remove(ws)
        WS_CONNECTED_CLIENTS.set(len(self.clients))

    async def broadcast(self, message: dict) -> None:
        dead_clients: list[WebSocket] = []
        for ws in self.clients:
            try:
                await ws.send_json(message)
            except Exception:
                dead_clients.append(ws)

        for ws in dead_clients:
            self.disconnect(ws)
