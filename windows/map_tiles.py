"""Shared OpenStreetMap tile request configuration for map windows."""

import hashlib
import io
import os

OSM_USER_AGENT = (
    "PreparationSimulation/1.0 "
    "(https://github.com/serafino1911/Preparation_Simulation)"
)
TILE_CACHE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tile_cache"
)


class _CachedResponse:
    def __init__(self, data):
        self.content = data
        self.raw = io.BytesIO(data)
        self.status_code = 200


class _RequestsWithCache:
    def __init__(self, original_requests):
        self._original_requests = original_requests

    def __getattr__(self, name):
        return getattr(self._original_requests, name)

    def get(self, url, **kwargs):
        cache_path = os.path.join(
            TILE_CACHE_DIR, hashlib.sha1(url.encode("utf-8")).hexdigest() + ".tile"
        )
        try:
            with open(cache_path, "rb") as cache_file:
                return _CachedResponse(cache_file.read())
        except OSError:
            pass

        headers = dict(kwargs.pop("headers", None) or {})
        headers["User-Agent"] = OSM_USER_AGENT
        headers.setdefault(
            "Referer", "https://github.com/serafino1911/Preparation_Simulation"
        )
        kwargs.pop("stream", None)
        response = self._original_requests.get(url, headers=headers, **kwargs)

        if response.status_code != 200 or not response.content:
            return response

        try:
            os.makedirs(TILE_CACHE_DIR, exist_ok=True)
            temporary_path = f"{cache_path}.{os.getpid()}.tmp"
            with open(temporary_path, "wb") as cache_file:
                cache_file.write(response.content)
            os.replace(temporary_path, cache_path)
        except OSError:
            pass

        return _CachedResponse(response.content)


def configure_tkintermapview():
    """Install the identifying User-Agent and persistent tile cache once."""
    import tkintermapview.map_widget as map_widget_module

    if getattr(map_widget_module.requests, "_preparation_simulation_tile_cache", False):
        return

    requests_with_cache = _RequestsWithCache(map_widget_module.requests)
    requests_with_cache._preparation_simulation_tile_cache = True
    map_widget_module.requests = requests_with_cache
