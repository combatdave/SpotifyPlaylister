import praw
import re
import spotipy
import sys


def GetSubmissionFromThread(threadurl):
    r = praw.Reddit(user_agent='combatdave spotifyplaylister')
    submission = r.get_submission(url=threadurl)
    return submission


def PopPunkify(text):
    abbreviations = {"tbs": "taking back sunday",
                     "tssf": "the story so far",
                     "twy": "the wonder years",
                     "fys": "four year strong",
                     "4ys": "four year strong",
                     "bmth": "bring me the horizon"}

    text = text.lower()
    for k, v in abbreviations.iteritems():
        text = text.replace(k, v)

    text = text.replace("by", "-")

    return text


def GetSongsFromSubmission(submission):
    bracketmatch = re.compile("\[(.*?)\]")
    flat_comments = praw.helpers.flatten_tree(submission.comments)

    bodies = [submission.selftext]
    bodies += [c.body for c in flat_comments]

    print len(bodies), "comments to look through..."

    allsongs = []
    for comment in bodies:
        # Strip out stuff in brackets
        comment = re.sub(r'\([^)]*\)', '', comment)

        comment = PopPunkify(comment)

        notmatched = []

        lines = comment.split("\n")
        for line in lines:
            line = line.strip()

            if "-" in line:
                m = re.search("[a-zA-Z]", line)
                if m:
                    line = line[m.start():]
                    allsongs.append(line)
            else:
                notmatched.append(line)

        notmatchedtext = "\r\n".join(notmatched)
        regexsongs = bracketmatch.findall(notmatchedtext)
        allsongs += regexsongs

    allsongs = [re.sub("[^0-9a-zA-Z']+", " ", s) for s in allsongs]

    return allsongs


def GetSongFromName(spotify, song):
    results = spotify.search(song, type="track")

    if len(results["tracks"]["items"]) > 0:
        firstresult = results["tracks"]["items"][0]
        return firstresult

    return None


def DoWork(auth_token, threadurl):
    sp = spotipy.Spotify(auth=auth_token)
    userid = sp.me()["id"]

    print "Loading thread " + threadurl + "..."

    submission = GetSubmissionFromThread(threadurl)
    submission_title = submission.title

    songnames = GetSongsFromSubmission(submission)

    if len(songnames) == 0:
        print "No songs found, giving up!"
        return [], [], None

    print "Found", len(songnames), "songs in thread " + submission_title + "..."

    playlist_name = "poppunkr: " + submission_title

    created_playlist = sp.user_playlist_create(userid, playlist_name)

    print "Created playlist '" + playlist_name + "'..."

    tracklist = []
    found = []
    notfound = []

    sys.stdout.write("Searching for songs on Spotify")
    for songname in songnames:
        songinfo = GetSongFromName(sp, songname)
        if songinfo is not None:
            tracklist.append(songinfo["uri"])
            found.append(songinfo)
        else:
            notfound.append(songname)
        sys.stdout.write(".")
    print ""

    sp.user_playlist_add_tracks(userid, created_playlist["id"], tracklist)

    print "Done!"
    if len(notfound) > 0:
        print "The following songs were not found. Are they spelled correctly?"
        for songname in notfound:
            print songname

    return found, notfound, created_playlist