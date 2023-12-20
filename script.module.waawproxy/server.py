import threading
from re import sub
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

import requests
import xbmc
import xbmcgui
from bottle import default_app, hook, request, response, route

app_name = "Waawproxy/0.7.0"


class SilentWSGIRequestHandler(WSGIRequestHandler):
    """Custom WSGI Request Handler with logging disabled"""

    protocol_version = "HTTP/1.1"

    def log_message(self, *args, **kwargs):
        """Disable log messages"""
        pass


class ThreadedWSGIServer(ThreadingMixIn, WSGIServer):
    """Multi-threaded WSGI server"""

    allow_reuse_address = True
    daemon_threads = True
    timeout = 1


def url():
    return xbmcgui.Window(10000).getProperty("waawproxy.url")


@hook("before_request")
def set_server_header():
    response.set_header("Server", app_name)


@route("/")
def index():
    response.content_type = "text/plain"
    return "Welcome to %s" % app_name


@route("/stream.m3u8")
def get_url():
    if not url():
        response.status = 500
        return "No URL set"
    headers = {
        "User-Agent": request.headers.get("User-Agent"),
        "Referer": request.headers.get("Referer"),
        "Origin": request.headers.get("Origin"),
    }
    resp = requests.get(url(), headers=headers)
    content = resp.text
    content = content.replace(
        "#EXTM3U",
        '#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=4364913,AVERAGE-BANDWIDTH=4277405,CODECS="avc1.4D4028,mp4a.40.2",RESOLUTION=1920x1080,AUDIO="AUDIO",FRAME-RATE=24',
    ).replace(".mp666", ".ts")
    base_path = "http://localhost:16969"
    content = sub(
        r"(#EXTINF:[0-9.]+,\n)([^#\n]+(?:\n|$))",
        r"\1%s/\2" % base_path,
        content,
    )
    response.content_type = "application/vnd.apple.mpegurl"
    response.status = resp.status_code
    return content


@route("/<path:path>")
def get_media(path):
    if not url():
        response.status = 500
        return "No URL set"
    media_url = url().rsplit("/", 1)[0] + "/" + path.replace(".ts", ".mp666")
    xbmc.log("[%s] Redirecting to %s" % (app_name, media_url), xbmc.LOGERROR)
    response.status = 302
    response.set_header("Location", media_url)
    return


class WebServerThread(threading.Thread):
    def __init__(self, httpd):
        threading.Thread.__init__(self)
        self.web_killed = threading.Event()
        self.httpd = httpd
        xbmc.log("[%s] Web server thread initialized" % app_name, xbmc.LOGERROR)

    def run(self):
        while not self.web_killed.is_set():
            self.httpd.handle_request()

    def stop(self):
        self.web_killed.set()


if __name__ == "__main__":
    if int(xbmc.getInfoLabel("System.BuildVersion").split(".")[0]) >= 20:
        xbmc.log(
            "[%s] No need to run webserver, Kodi 20+ supports HLS properly" % app_name,
            xbmc.LOGERROR,
        )
        exit(0)
    app = default_app()
    try:
        httpd = make_server(
            "127.0.0.1",
            16969,
            app,
            server_class=ThreadedWSGIServer,
            handler_class=SilentWSGIRequestHandler,
        )
    except OSError as e:
        if e.errno == 98:
            xbmc.log(
                "[%s] Port %s is already in use." % (app_name, 16969),
                xbmc.LOGERROR,
            )
            dialog = xbmcgui.Dialog()
            dialog.notification(
                "Port Error",
                "Port %s is already in use. Please close any other instances of Kodi and try again."
                % 16969,
                xbmcgui.NOTIFICATION_ERROR,
                10000,
            )
            exit(1)
        raise
    web_thread = WebServerThread(httpd)
    web_thread.start()
    xbmc.log("[%s] Web server started" % app_name, xbmc.LOGERROR)
    monitor = xbmc.Monitor()
    while not monitor.abortRequested():
        xbmc.sleep(100)
    xbmc.log("[%s] Exiting webserver" % app_name, xbmc.LOGERROR)
    web_thread.stop()
    web_thread.join()
