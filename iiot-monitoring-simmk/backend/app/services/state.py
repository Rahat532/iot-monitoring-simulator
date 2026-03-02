from app.services.ws_manager import WSManager

ws_manager = WSManager()
latest_cache: list[dict] = []
MAX_CACHE = 500
