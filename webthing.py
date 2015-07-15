import SimpleHTTPServer
import SocketServer
import spotipy.oauth2 as oauth2
from urlparse import urlparse
import urllib
from main import DoWork

access_token = None

class MyRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    # Janky as fuck
    threadurl = None
    sp_oauth = None

    def GetAuthURLOrSetAccessToken(self):
        username = "combatdave spotifyplaylister"
        scope = "playlist-modify-public"
        client_id = "c8759f93400544fe9b75807942a593ba"
        client_secret = "944fc356cb214c72a9a97772ded6d6c2"
        redirect_uri = "http://127.0.0.1:8080/callback/"

        if MyRequestHandler.sp_oauth is None:
            MyRequestHandler.sp_oauth = oauth2.SpotifyOAuth(client_id, client_secret, redirect_uri, scope=scope, cache_path=".cache-" + username)

        token_info = MyRequestHandler.sp_oauth.get_cached_token()

        if not token_info:
            auth_url = MyRequestHandler.sp_oauth.get_authorize_url()
            return auth_url
        else:
            global access_token
            access_token = token_info["access_token"]
            return None


    def DoLoginPage(self, url):
        with open("login.html") as f:
            self.send_response(200)

            self.send_header('Content-type','text-html')
            self.end_headers()

            contents = f.read()
            contents = contents.format(url=url)
            self.wfile.write(contents)


    def HandleCallback(self, response):
        print "Got code:", response

        code = MyRequestHandler.sp_oauth.parse_response_code(response)
        token_info = MyRequestHandler.sp_oauth.get_access_token(code)

        global access_token
        access_token = token_info['access_token']


    def DoActualWork(self):
        self.path = "/" + MyRequestHandler.threadurl

        self.send_response(200)

        self.send_header('Content-type', 'text-html')
        self.end_headers()

        with open("result.html") as f:
            global access_token
            found, notfound, created_playlist = DoWork(access_token, MyRequestHandler.threadurl)

            notfoundlist = "<ul>"
            for songname in notfound:
                notfoundlist += "<li>" + songname + "</li>"
            notfoundlist += "</ul>"

            template = f.read()
            output = template.format(numfound=len(found),
                           playlisturl=created_playlist["external_urls"]["spotify"],
                           playlistname=created_playlist["name"],
                           numnotfound=len(notfound),
                           notfoundlist=notfoundlist
                          )

            self.wfile.write(output)


    def LoginOrDoWork(self):
        global access_token
        if access_token is None:
            auth_url = self.GetAuthURLOrSetAccessToken()
            if auth_url is not None:
                return self.DoLoginPage(auth_url)
        return self.DoActualWork()


    def do_GET(self):
        splitpath = self.path.split("/")[1:]
        print splitpath
        if len(splitpath) == 2:
            if splitpath[0] == "callback":
                self.HandleCallback(splitpath[1])
                return self.DoActualWork()
        else:
            onlypath = urlparse(self.path).path
            if onlypath == "/thread":
                query = urlparse(self.path).query
                query_components = dict(qc.split("=") for qc in query.split("&"))
                if "url" in query_components:
                    MyRequestHandler.threadurl = urllib.unquote(query_components["url"])
                    return self.LoginOrDoWork()

        return SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)


server = SocketServer.TCPServer(('0.0.0.0', 8080), MyRequestHandler)

print "http://127.0.0.1:8080/"

server.serve_forever()
