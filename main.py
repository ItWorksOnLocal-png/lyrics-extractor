import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
import time
from click import pause
import os


def pip_install(module: str):
    subprocess.run([sys.executable, "-m", "pip", "-q", "--disable-pip-version-check", "install", module])


try:
    import certifi
except:
    print("Installing required Modules... Only for first time... ")
    pip_install("certifi")
    import certifi

try:
    import requests
except:
    print("Installing required Modules... Only for first time... ")
    pip_install("requests")
    import requests

try:
    import urllib3
except:
    print("Installing required Modules... Only for first time... ")
    pip_install("urllib3")
    import urllib3

try:
    from bs4 import BeautifulSoup
except:
    print("Installing required Modules... Only for first time... ")
    pip_install("bs4")
    from bs4 import BeautifulSoup


class GetLyrics:
    def __init__(self):
        self.title = None
        self.artist = None
        self.lyrics = None
        self.source = None
        self.query = None
        self.api_key = None
        self.url = None

    def google_lyrics(self, query):
        query = str(query)
        try:
            url = "https://www.google.com/search?q=" + query.replace(" ", "+") + "+lyrics"

            r = requests.get(url)
            htmlcontent = r.content
            html_content = BeautifulSoup(htmlcontent, "html.parser")

            title = str(html_content.find("span", class_="BNeawe tAd8D AP7Wnd"))
            title = re.sub(r"(<.*?>)*", "", title).replace("[", "").replace("]", "")

            artist = html_content.find_all("span", class_="BNeawe s3v9rd AP7Wnd")
            artist = str(artist[1])
            artist = re.sub(r"(<.*?>)*", "", artist).replace("[", "").replace("]", "")

            lyrics = html_content.find_all("div", class_="BNeawe tAd8D AP7Wnd")
            lyrics = str(lyrics[2])
            lyrics = re.sub(r"(<.*?>)*", "", lyrics).replace("[", "").replace("]", "")

            source = str(html_content.find("span", class_="uEec3 AP7Wnd"))
            source = re.sub(r"(<.*?>)*", "", source).replace("[", "").replace("]", "")

            if lyrics is None or artist is None or title is None or source is None:
                raise Exception("Something went wrong. No lyrics yielded. ")

            self.title = title  # Name of the track
            self.artist = artist  # Name of the artist
            self.lyrics = lyrics  # Lyrics of the track
            self.source = source  # Source of the lyrics
            self.query = query  # Query requested by the user
            self.api_key = None  # API Key provided by the user (Here not required)
            self.url = None
        except:
            raise Exception

    def genius_lyrics(self, query, api_key):
        query = str(query)
        api_key = str(api_key)
        try:
            url = "https://api.genius.com/search?access_token=" + api_key + "&q=" + query.replace("&",
                                                                                                  "and").replace(
                "by", "-").replace(" ", "%20")
            details = urllib.request.urlopen(url).read().decode()
            json_results = json.loads(details)

            title = str(json_results["response"]["hits"][0]["result"]["title"])
            artist = str(json_results["response"]["hits"][0]["result"]["primary_artist"]["name"])
            genius_url = str(json_results["response"]["hits"][0]["result"]["url"])
            url1 = genius_url
            r = requests.get(url1)
            htmlcontent = r.content
            html_content = BeautifulSoup(htmlcontent.decode("utf-8").replace("<br/>", "\n"), "html.parser")
            
            lyrics = str(html_content.find("div", class_=re.compile("^lyrics$|Lyrics__Root")))
            lyrics = re.sub(r"(<.*?>)*", "", lyrics)
            lyrics = re.sub(r"(\[.*?])*", "", lyrics).strip()
            lyrics = lyrics.replace("EmbedShare Url:CopyEmbed:Copy", "").replace("EmbedShare URLCopyEmbedCopy", "").strip()
            lyrics = re.sub('\n\n+', '\n\n', lyrics)

            self.title = title  # Name of the track
            self.artist = artist  # Name of the artist
            self.lyrics = lyrics  # Lyrics of the track
            self.source = "Genius"  # Source of the lyrics
            self.query = query  # Query requested by the user
            self.api_key = api_key  # API Key provided by the user
            self.url = url1
        except:
            raise Exception

    def musixmatch_lyrics(self, query):  # sourcery skip: raise-specific-error
        query = str(query)
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)      Chrome/74.0.3729.169 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                'Accept-Encoding': 'none',
                'Accept-Language': 'en-US,en;q=0.8',
                'Connection': 'keep-alive'}
            url = 'https://www.musixmatch.com/search/' + query.replace(" ", "%20")  # +'/lyrics'
            http = urllib3.PoolManager(ca_certs=certifi.where())
            resp = http.request('GET', url, headers=headers)
            r = resp.data.decode('utf-8')
            html_content = BeautifulSoup(r, "html.parser")
            href = str(html_content.find("a", class_="title")).split("href=")[1].split('''"''')[1]
            new_link = "https://www.musixmatch.com/" + href
            http = urllib3.PoolManager(ca_certs=certifi.where())
            url = new_link
            resp = http.request('GET', url, headers=headers)
            r = resp.data.decode('utf-8')
            html_content = BeautifulSoup(r, "html.parser")

            artist = str(html_content.find("a", class_="mxm-track-title__artist mxm-track-title__artist-link"))
            artist = re.sub(r"(<.*?>)*", "", artist)

            title = str(html_content.find("h1", class_="mxm-track-title__track").getText("//")).split("//")[-1]
            title = re.sub(r"(<.*?>)*", "", title)

            lyrics = html_content.findAll("span", class_="lyrics__content__ok")
            lyrics = str(lyrics[0]) + "\n" + str(lyrics[1])
            lyrics = re.sub(r"(<.*?>)*", "", lyrics)

            self.title = title  # Name of the track
            self.artist = artist  # Name of the artist
            self.lyrics = lyrics  # Lyrics of the track
            self.source = "Musixmatch"  # Source of the lyrics
            self.query = query  # Query requested by the user
            self.api_key = None  # API Key provided by the user
            self.url = new_link
        except:
            raise Exception


def get_lyrics(full_title, genius_client_secret_api):
    # sourcery skip: inline-immediately-returned-variable
    query_title = str(full_title)  # .encode('utf-8')
    query_title = re.sub(r'[^\w]', ' ', query_title)
    query_title = re.sub(' +', ' ', query_title)
    ly = GetLyrics()
    try:
        ly.musixmatch_lyrics(query_title)
    except:
        try:
            ly.google_lyrics(query_title)
        except:
            ly.genius_lyrics(query_title, genius_client_secret_api)
    lyrics = f"""
---------------------------------

{ly.title}
{ly.artist}


{ly.lyrics}


---------------------------------
Lyrics provided by {ly.source}
---------------------------------
"""
    print(lyrics)
    pause("\nPress any key to go back...")


# sourcery skip: merge-comparisons
genius_api_key = "zENbut92U1YJeKVMYcJtCZFq_93qCGBbkld0xusupTlrMO1mlV2t46k8-puK6SXI"

while True:
    os.system('cls')
    print('''
 ██████╗ ███████╗████████╗    ████████╗██╗  ██╗███████╗    ██╗  ██╗   ██╗██████╗ ██╗ ██████╗███████╗
██╔════╝ ██╔════╝╚══██╔══╝    ╚══██╔══╝██║  ██║██╔════╝    ██║  ╚██╗ ██╔╝██╔══██╗██║██╔════╝██╔════╝
██║  ███╗█████╗     ██║          ██║   ███████║█████╗      ██║   ╚████╔╝ ██████╔╝██║██║     ███████╗
██║   ██║██╔══╝     ██║          ██║   ██╔══██║██╔══╝      ██║    ╚██╔╝  ██╔══██╗██║██║     ╚════██║
╚██████╔╝███████╗   ██║          ██║   ██║  ██║███████╗    ███████╗██║   ██║  ██║██║╚██████╗███████║
 ╚═════╝ ╚══════╝   ╚═╝          ╚═╝   ╚═╝  ╚═╝╚══════╝    ╚══════╝╚═╝   ╚═╝  ╚═╝╚═╝ ╚═════╝╚══════╝
=====================================================================================================
\n''')
    query = input("Enter track name of what you want lyrics: ")
    if query.strip().lower() == "quit" or query.strip().lower() == "exit" or query.strip().lower() == "break":
        print("\n\nExiting in 10 seconds. ")
        time.sleep(10)
        break
    else:
        try:
            print("Searching, hold on...\n")
            print(get_lyrics(query, genius_api_key))
        except:
            print("Something went wrong, make sure the track has lyrics or you have active internet connection \n"
                  "or the given Genius Client Secret is correct or try to be more specific and check typo. \n\n")
