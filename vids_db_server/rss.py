"""
    Generates an rss stream from a list of VideoInfo object.
"""

from typing import List

import feedparser  # type: ignore
from vids_db.models import Video  # type: ignore

from vids_db_server.date import iso_fmt


def _rss_item(vid_info: Video) -> str:
    views = "0" if vid_info.views == "?" else vid_info.views

    def cdata(inner: str) -> str:
        return f"<![CDATA[{inner}]]>"
        # return instr

    description = cdata(vid_info.description)
    title = cdata(vid_info.title)
    channel_name = cdata(vid_info.channel_name)
    return f"""    <item>
      <title>{title}</title>
      <pubDate>{iso_fmt(vid_info.date_published)}</pubDate>
      <lastupdated>{iso_fmt(vid_info.date_lastupdated)}</lastupdated>
      <link>{vid_info.url}</link>
      <channel_url>{vid_info.channel_url}</channel_url>
      <channel_name>{channel_name}</channel_name>
      <description>{description}</description>
      <thumbnail>{vid_info.img_src}</thumbnail>
      <dc:creator>{vid_info.channel_name}></dc:creator>
      <duration>{vid_info.duration}</duration>
      <views>{views}</views>
      <host>{vid_info.source}</host>
      <iframe>{vid_info.iframe_src}</iframe>
    </item>
"""


def to_rss(title: str, vid_list: List[Video]) -> str:
    """
    Returns a list of RSS items as a string.
    """
    out = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/">
"""
    out += "  <channel>\n"
    out += f"    <title>{title}</title>"
    for video in vid_list:
        out += _rss_item(video)
    out += "  </channel>\n"
    out += "</rss>"
    return out


def from_rss(rss_str: str) -> List[Video]:
    """
    Returns a list of VideoInfo objects from an RSS stream.
    """
    out: List[Video] = []
    parsed = feedparser.parse(rss_str)
    for entry in parsed.entries:
        vid = Video(
            channel_name=entry.channel_name,
            title=entry.title,
            date_published=iso_fmt(entry.published),
            date_lastupdated=iso_fmt(entry.lastupdated),
            channel_url=entry.channel_url,
            source=entry.host,
            url=entry.link,
            img_src=entry.thumbnail,
            iframe_src=entry.iframe,
            views=entry.views,
            duration=entry.duration,
            description=entry.description,
        )
        out.append(vid)
    return out
