"""
    Flask app for the ytclip command line tool. Serves an index.html at port 80. Clipping
    api is located at /clip
"""
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import (
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
    Response,
)
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel  # pylint: disable=no-name-in-module
from vids_db.database import Database  # type: ignore
from vids_db.date import parse_datetime  # type: ignore
from vids_db.models import Video  # type: ignore

from vids_db_server.rss import from_rss, to_rss

# from vids_db.database import Database
from vids_db_server.version import VERSION

MODE = os.environ.get("MODE", "DEVELOPMENT")
IS_PRODUCTION = MODE == "PRODUCTION"

DB_PATH = os.environ.get("DB_PATH_DIR", None)
HERE = os.path.dirname(os.path.abspath(__file__))


if MODE == "PRODUCTION" and os.environ.get("API_KEY") is None:
    raise Exception(
        "API_KEY environment variable must be set in production mode"
    )

executor = ThreadPoolExecutor(max_workers=8)
vids_db = Database(DB_PATH)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

STARTUP_DATETIME = datetime.now()


class MultiChannelJsonQuery(
    BaseModel
):  # pylint: disable=too-few-public-methods
    """Query structure."""

    hours_ago: int = 24
    channel_names: List[str]


class RssResponse(Response):  # pylint: disable=too-few-public-methods
    """Returns an RSS response from a query."""

    media_type = "application/rss+xml"


def valid_api_key(api_key: Optional[str]) -> bool:
    """Checks if the api key is valid."""
    if "API_KEY" in os.environ:
        return api_key == os.environ.get("API_KEY")
    return True


def log_error(msg: str) -> None:
    """Logs an error to the print stream."""
    print(msg)


# Mount all the static files.
app.mount("/www", StaticFiles(directory=os.path.join(HERE, "www")), "www")


# Redirect to index.html
@app.get("/")
async def index() -> RedirectResponse:
    """Returns index.html file"""
    # return RedirectResponse(url="/www/index.html", status_code=302)
    return RedirectResponse(url="/docs", status_code=302)


# Redirect to favicon.ico
@app.get("/favicon.ico")
async def favicon() -> RedirectResponse:
    """Returns favico file."""
    return RedirectResponse(url="/www/favicon.ico")


@app.get("/info")
async def api_info() -> PlainTextResponse:
    """Api endpoint for getting the version."""
    out = f"VERSION: {VERSION}\nMODE: {MODE}\n"
    return PlainTextResponse(out)


@app.get("/search")
async def api_search(query: str) -> JSONResponse:
    """Api endpoint for getting the version."""
    vids = vids_db.query_video_list(query)
    json_vids = [v.to_json() for v in vids]
    return JSONResponse(json_vids)


@app.get("/rss")
async def api_rss_channel_feed(channel: str) -> RssResponse:
    """Api endpoint for adding a video"""
    now = datetime.now()
    start = now - timedelta(days=7)
    out = vids_db.get_video_list(start, now, channel)
    return RssResponse(to_rss(title=channel, vid_list=out))


@app.get("/rss/all")
async def api_rss_all_feed(hours_ago: int) -> RssResponse:
    """Api endpoint for adding a video"""
    now = datetime.now()
    hours_ago = min(max(0, hours_ago), 48)
    start = now - timedelta(hours=hours_ago)
    out = vids_db.get_video_list(start, now)
    return RssResponse(to_rss(title="AllVids", vid_list=out))


@app.get("/json")
async def api_json_channel_feed(
    channel: str, days: Optional[int] = None, limit: Optional[int] = None
) -> JSONResponse:
    """Api endpoint for adding a video"""
    now = datetime.now()
    days = days or 30
    limit = limit or 100
    start = now - timedelta(days=7)
    vids = vids_db.get_video_list(start, now, channel, limit)
    json_vids = [v.to_json() for v in vids]
    return JSONResponse(json_vids)


@app.post("/json/many")
async def api_json_multi(query: MultiChannelJsonQuery) -> JSONResponse:
    """Api endpoint for adding a video"""
    now = datetime.now()
    start = now - timedelta(hours=query.hours_ago)
    print(query.channel_names)
    vids = []
    for channel in query.channel_names:
        vids += vids_db.get_video_list(start, now, channel)
    json_vids = [v.to_json() for v in vids]
    # Sort json_vids by date_published
    json_vids.sort(
        key=lambda v: parse_datetime(v["date_published"]).timestamp(),
        reverse=True,
    )
    return JSONResponse(json_vids)


@app.get("/json/all")
async def api_json_all_feed(hours_ago: int) -> JSONResponse:
    """Api endpoint for adding a video"""
    now = datetime.now()
    hours_ago = min(max(0, hours_ago), 48)
    start = now - timedelta(hours=hours_ago)
    vids = vids_db.get_video_list(start, now)
    json_vids = [v.to_json() for v in vids]
    return JSONResponse(json_vids)


@app.put("/put/video")
async def api_add_video(
    video: Video, api_key: Optional[str] = Header(None)
) -> JSONResponse:
    """Api endpoint for adding a snapshot."""
    if not valid_api_key(api_key):
        return JSONResponse({"ok": False, "error": "Invalid API key"})
    vids_db.update(video)
    return JSONResponse({"ok": True, "msg": "updated 1 video"})


@app.put("/put/videos")
async def api_add_videos(
    videos: List[Video], api_key: Optional[str] = Header(None)
) -> JSONResponse:
    """Api endpoint for adding a snapshot."""
    if not valid_api_key(api_key):
        return JSONResponse({"ok": False, "error": "Invalid API key"})
    vids_db.update_many(videos)
    return JSONResponse({"ok": True, "msg": f"updated {len(videos)} videos"})


@app.put("/put/rss")
async def api_put_rss(
    rss_str: str, api_key: Optional[str] = Header(None)
) -> JSONResponse:
    """Api endpoint for adding a snapshot from rss"""
    if not valid_api_key(api_key):
        return JSONResponse({"ok": False, "error": "Invalid API key"})
    vids = from_rss(rss_str)
    vids_db.update_many(vids)
    return JSONResponse({"ok": True})


if not IS_PRODUCTION:

    @app.post("/test/clear/videos")
    async def clear_videos() -> JSONResponse:
        """Api endpoint for adding a snapshot."""
        # vids_db.clear()
        return JSONResponse({"ok": True})
