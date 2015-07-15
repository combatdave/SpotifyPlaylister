from flask import Flask
from flask import render_template, request, redirect, send_file, Response
import spotipy.oauth2 as oauth2
import ConfigParser
from main import DoWork

app = Flask(__name__)

sp_oauth = None

threadurl = None
access_token = None


def GetSpotifyAuth():
    global sp_oauth

    if sp_oauth is None:
        username = "poppunkr"
        scope = "playlist-modify-public"

        config = ConfigParser.ConfigParser()
        config.read("config.ini")
        client_id = config.get("spotify", "clientid")
        client_secret = config.get("spotify", "clientsecret")
        redirect_uri = config.get("spotify", "redirecturl")

        sp_oauth = oauth2.SpotifyOAuth(client_id, client_secret, redirect_uri, scope=scope, cache_path=".cache-" + username)

    return sp_oauth

@app.route("/")
def index():
    return render_template('index.html')


@app.route("/thread")
def ParseThread(url=None):
    global threadurl, access_token
    threadurl = request.args.get("url")

    login = DoLogin()
    if login is not None:
        return login

    return Output()


def Output():
    found, notfound, created_playlist = DoWork(access_token, threadurl)

    if created_playlist is not None:
        return render_template("result.html",
                   playlisturl=created_playlist["external_urls"]["spotify"],
                   playlistname=created_playlist["name"],
                   numfound=len(found),
                   numnotfound=len(notfound),
                   notfoundlist=notfound
                  )
    else:
        return render_template("badnews.html", errortext="We couldn't find any songs in that thread :(")


@app.route("/callback")
def Callback():
    spotify_auth = GetSpotifyAuth()

    response_code = request.args.get("code")
    token_info = spotify_auth.get_access_token(response_code)

    global access_token
    access_token = token_info['access_token']

    global threadurl
    return redirect("/thread?url=" + threadurl)


def DoLogin():
    spotify_auth = GetSpotifyAuth()
    token_info = spotify_auth.get_cached_token()

    if not token_info:
        auth_url = spotify_auth.get_authorize_url()
        return redirect(auth_url)
    else:
        global access_token
        access_token = token_info["access_token"]
        return None


if __name__ == "__main__":
    app.run(debug=True)