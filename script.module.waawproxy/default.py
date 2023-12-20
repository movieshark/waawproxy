import xbmcgui
import xbmc
from sys import argv
from xbmcaddon import Addon
from xbmcplugin import setResolvedUrl

try:
    from urllib.parse import parse_qsl
except ImportError:
    from urlparse import parse_qsl

addon = Addon()
addon_name = addon.getAddonInfo("name")

if __name__ == "__main__":
    if len(argv) < 3:
        dialog = xbmcgui.Dialog()
        dialog.ok(
            addon_name,
            "This addon is not meant to be run directly.[CR]"
            "Call this using %s/?url=<url>" % argv[0],
        )
    params = dict(parse_qsl(argv[2].replace("?", "")))
    video_url = params.get("url")
    if not video_url:
        dialog = xbmcgui.Dialog()
        dialog.ok(
            addon_name, "No URL provided[CR]" "Call this using %s/?url=<url>" % argv[0]
        )
    headers = video_url.split("|")[1]
    li = xbmcgui.ListItem()
    li.setProperty("inputstream", "inputstream.adaptive")
    li.setProperty("inputstream.adaptive.manifest_type", "hls")
    li.setProperty("inputstream.adaptive.stream_headers", headers)
    li.setProperty("inputstream.adaptive.manifest_headers", headers)
    li.setMimeType("application/vnd.apple.mpegurl")
    li.setContentLookup(False)
    if int(xbmc.getInfoLabel("System.BuildVersion").split(".")[0]) < 20:
        xbmcgui.Window(10000).setProperty("waawproxy.url", video_url.split("|")[0])
        li.setPath("http://localhost:16969/stream.m3u8" + "|" + headers)
    else:
        li.setPath(video_url)
    setResolvedUrl(int(argv[1]), True, li)
