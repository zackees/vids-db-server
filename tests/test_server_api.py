"""
Tests the fastapi server.
"""

# pylint: disable=invalid-name,R0801

import os
import shutil
import unittest

import requests  # type: ignore
from vids_db.date import now_local  # type: ignore
from vids_db.models import Video  # type: ignore
from vids_db_server.testing.run_server_in_thread import (  # type: ignore
    HOST,
    PORT,
    run_server_in_thread,
)

# In our testing environment we use the same database for all tests.
HERE = os.path.dirname(os.path.abspath(__file__))
TEST_DB = os.path.join(HERE, "data")
TEST_DATA_JSON = os.path.join(HERE, "test_data.json")
REMOTE_ENDPOINT = f"http://{HOST}:{PORT}"

if os.path.exists(TEST_DB):
    shutil.rmtree(TEST_DB, ignore_errors=True)

os.environ.update({"DB_PATH_DIR": TEST_DB})


def make_vid(channel_name: str, title: str) -> Video:
    """Generates a video with default values."""
    return Video(
        channel_name=channel_name,
        title=title,
        date_published=now_local(),
        date_lastupdated=now_local(),
        channel_url=f"{REMOTE_ENDPOINT}/channel/{channel_name}",
        source="rumble.com",
        url=f"{REMOTE_ENDPOINT}/video/{title}",
        img_src=f"{REMOTE_ENDPOINT}/img/{title}.png",
        iframe_src=f"{REMOTE_ENDPOINT}/iframe/{title}",
        views=100,
        duration=60,
        description="",
    )


class ApiServerTester(unittest.TestCase):
    """Tester for the vids_db_server."""

    def test_platform_put_get(self) -> None:
        """Opens up the vids_db and tests that the version returned is correct."""
        with run_server_in_thread():
            vid = make_vid("test_channel", "test_title")
            r = requests.put(f"{REMOTE_ENDPOINT}/put/video", json=vid.to_json(), timeout=30)
            r.raise_for_status()
            r = requests.get(f"{REMOTE_ENDPOINT}/rss/all?hours_ago=24", timeout=30)
            r.raise_for_status()

    def test_put_videos(self) -> None:
        """Tests the ingestment of the data"""

        headers = {
            "accept": "application/json",
            # Already added when you pass json= but not when you pass data=
        }

        json_data = [
            {
                "channel_name": "string",
                "title": "string",
                "date_published": "2022-05-13T02:02:31.296Z",
                "date_lastupdated": "2022-05-13T02:02:31.296Z",
                "channel_url": "http://example.com",
                "source": "string",
                "url": "http://example.com",
                "duration": 0,
                "description": "string",
                "img_src": "http://example.com",
                "iframe_src": "http://example.com",
                "views": 0,
            },
        ]
        with run_server_in_thread():
            response = requests.put(
                f"{REMOTE_ENDPOINT}/put/videos",
                headers=headers,
                json=json_data,
                timeout=30,
            )
            response.raise_for_status()


if __name__ == "__main__":
    unittest.main()
