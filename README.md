# waawproxy

A hacky workaround to get Kodi versions below 20 to play WAAW streams.

## Motivation

HLS streams are laggy and unreliable for some reason with the built-in player across all versions of Kodi we tried. So we switched to inputstream.adaptive, which works great on Kodi 20.2. However some users reported that waaw links won't play on Kodi 19.5 and below. Turns out that the provider uses `.mp666` as the extension for the segments in the manifest files and inputstream.adaptive doesn't like that as it tries to assume the segment type from the extension on the older versions of Kodi.

This extension tries to work around that by rewriting the manifest files on the fly and replacing the `.mp666` extension with `.ts`. We also need to redirect the segments to the proxy, but a simple 302 redirect is enough then to make inputstream.adaptive happy. So this is essentially a proxy that rewrites the manifest files and redirects the segments.

## Example usage

Note: You will need to install the `resolveurl` addon for this to work.

```py
import xbmcgui
import resolveurl
try:
    from urllib.parse import parse_qsl, urlencode
except ImportError:
    from urlparse import parse_qsl
    from urllib import urlencode
from sys import argv
import xbmcplugin

direct_url = resolveurl.resolve("https://waaw.to/f/RSemGPv4ycy4")

if __name__ == "__main__":
    params = dict(parse_qsl(argv[2].replace("?", "")))
    action = params.get("action")
    if not action:
        li = xbmcgui.ListItem("Test")
        li.setContentLookup(False)
        li.setProperty("IsPlayable", "true")
        li.setInfo("video", {"title": "Test"})
        url = "plugin://script.module.waawproxy/?" + urlencode(
            {"url": direct_url}
        )
        xbmcplugin.addDirectoryItem(
            handle=int(argv[1]),
            url=url,
            listitem=li,
            isFolder=False,
        )
        xbmcplugin.endOfDirectory(int(argv[1]))
```