"""
    Flask app for the ytclip command line tool. Serves an index.html at port 80. Clipping
    api is located at /clip
"""
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI
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
from vids_db.models import Video  # type: ignore

from vids_db_server.rss import to_rss

# from vids_db.database import Database
from vids_db_server.version import VERSION

IS_PRODUCTION = os.environ.get("MODE") == "PRODUCTION"

DB_PATH = os.environ.get("DB_PATH_DIR", None)
HERE = os.path.dirname(os.path.abspath(__file__))

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


class RssResponse(Response):  # pylint: disable=too-few-public-methods
    """Returns an RSS response from a query."""

    media_type = "application/rss+xml"


class Query(BaseModel):  # pylint: disable=too-few-public-methods
    """Query structure."""

    start: datetime
    end: datetime
    channel_names: Optional[List[str]] = None
    limit: int = -1


class RssQuery(BaseModel):  # pylint: disable=too-few-public-methods
    """Query structure."""

    channel_name: str
    days: int = 7
    limit: int = -1


def log_error(msg: str) -> None:
    """Logs an error to the print stream."""
    print(msg)


# Mount all the static files.
app.mount("/www", StaticFiles(directory=os.path.join(HERE, "www")), "www")


# Redirect to index.html
@app.get("/")
async def index() -> RedirectResponse:
    """Returns index.html file"""
    return RedirectResponse(url="/www/index.html", status_code=302)


# Redirect to favicon.ico
@app.get("/favicon.ico")
async def favicon() -> RedirectResponse:
    """Returns favico file."""
    return RedirectResponse(url="/www/favicon.ico")


@app.get("/version")
async def api_version() -> PlainTextResponse:
    """Api endpoint for getting the version."""
    return PlainTextResponse(VERSION)


@app.post("/query")
async def api_query(query: Query) -> JSONResponse:
    """Api endpoint for adding a video"""
    out: List[Video] = []
    if query.channel_names is None:
        query.channel_names = []
        out.extend(
            vids_db.get_video_list(query.start, query.end, None, query.limit)
        )
    else:
        for channel_name in query.channel_names:
            data = vids_db.get_video_list(
                query.start, query.end, channel_name, query.limit
            )
            out.extend(data)
    return JSONResponse(Video.to_plain_list(out))


@app.post("/rss", response_model=List[Video])
async def api_rss_channel_feed(query: RssQuery) -> RssResponse:
    """Api endpoint for adding a video"""
    now = datetime.now()
    start = now - timedelta(days=query.days)
    kwargs = {}
    if query.limit > 0:
        kwargs["limit"] = query.limit
    out = vids_db.get_video_list(start, now, query.channel_name, **kwargs)
    return RssResponse(to_rss(out))


@app.get("/rss/all", response_model=List[Video])
async def api_rss_all_feed(hours_ago: int) -> RssResponse:
    """Api endpoint for adding a video"""
    now = datetime.now()
    hours_ago = min(hours_ago, 48)
    start = now - timedelta(hours=hours_ago)
    out = vids_db.get_video_list(start, now)
    return RssResponse(to_rss(out))


@app.put("/put/video")
async def api_add_video(video: Video) -> JSONResponse:
    """Api endpoint for adding a snapshot."""
    vids_db.update(video)
    return JSONResponse({"ok": True})


@app.put("/put/videos")
async def api_add_videos(videos: List[Video]) -> JSONResponse:
    """Api endpoint for adding a snapshot."""
    vids_db.update_many(videos)
    return JSONResponse({"ok": True})


if not IS_PRODUCTION:

    @app.put("/test/put/videos")
    async def add_test_videos() -> JSONResponse:
        """Api endpoint for adding a snapshot."""
        with open(
            os.path.join(HERE, "testing", "test_data.json"),
            encoding="utf-8",
            mode="r",
        ) as filep:
            data = filep.read()
        data = Video.from_list_of_dicts(json.loads(data).get("content"))
        vids_db.update_many(data)
        return JSONResponse({"ok": True})

    @app.put("/test/put/video_with_json")
    async def add_test_videos_with_json(json_str: str) -> JSONResponse:
        """Api endpoint for adding a snapshot."""
        vids = Video.parse_json_str(json_str)
        vids_db.update(vids)
        return JSONResponse({"ok": True})

    @app.post("/test/clear/videos")
    async def clear_videos() -> JSONResponse:
        """Api endpoint for adding a snapshot."""
        # vids_db.clear()
        return JSONResponse({"ok": True})
