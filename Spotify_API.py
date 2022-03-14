from selenium import webdriver
import selenium.webdriver.support.ui as ui
import base64
import credentials
import requests
import json
import time
from datetime import datetime

def store_credentials(name, value):

    credentials = open("credentials.py", "a")

    credentials.write('\n' + name + " = '" + str(value)+"'")

def get_code(redirect_uri, client_id):
    
    url = "https://accounts.spotify.com/authorize?response_type=code&client_id={}&scope=user-read-recently-played&redirect_uri={}".format(client_id, redirect_uri)
    
    driver = webdriver.Chrome()
    
    driver.get(url)

    wait = ui.WebDriverWait(driver, 180)

    wait.until(lambda driver: driver.current_url[:len(redirect_uri)] == redirect_uri)

    code = driver.current_url.split('code=')[1][:200]

    driver.close()

    store_credentials("code", code)

    return code

def base64_encode(id, secret):

    data = id + ":" + secret

    string_bytes = data.encode("ascii")

    base64_bytes = base64.b64encode(string_bytes)

    encoded_data = base64_bytes.decode("ascii")

    return encoded_data

def get_refreshable_token(code, redirect_uri, client_id, client_secret, url):

    body = {
        "grant_type" : "authorization_code",
        "code" : code,
        "redirect_uri" : redirect_uri,
    }

    headers = {
        "Authorization" : "Basic " + base64_encode(client_id, client_secret),
        "Content_Type" : "application/x-www-form-urlencoded"
    }

    post_request = requests.post(url, headers = headers, data = body)

    refreshable_token = post_request.json()['refresh_token']

    store_credentials("refreshable_token", refreshable_token)

    return refreshable_token

def refresh_token(refreshable_token, client_id, client_secret, url):

    body = {
        "grant_type" : "refresh_token",
        "refresh_token" : refreshable_token
    }

    headers = {
        "Authorization" : "Basic " + base64_encode(client_id, client_secret),
        "Content_Type" : "application/x-www-form-urlencoded"
    }

    post_request = requests.post(url, headers = headers, data = body)

    new_token = post_request.json()['access_token']

    return new_token

def get_recently_played(token, timestamp):

    if timestamp == "":

        url = "https://api.spotify.com/v1/me/player/recently-played?limit=50"

    else:

        url = "https://api.spotify.com/v1/me/player/recently-played?limit=50&after={}".format(timestamp)

    headers = {
        "Accept" : "application/json",
        "Content_Type" : "application/json",
        "Authorization" : "Bearer " + token,
    }

    get_request = requests.get(url, headers = headers)

    recently_played = get_request.json()

    return recently_played


def get_after_timestamp(json, timestamp):

    if json['cursors'] == None:

        return timestamp

    else:

        timestamp = json['cursors']['after']

        return timestamp

def save_data(data):

    extract_time = datetime.now().strftime("%d.%m.%Y-%H.%M")

    filename = 'recentlyPlayed_{}.json'.format(extract_time)

    if len(data['items']) > 0:

        with open(filename, 'w', encoding='utf-8') as f:

            json.dump(data, f, ensure_ascii=False, indent=4)

        return

def get_data(refreshable_token, client_id, client_secret, url, timestamp):

    while(True):

        token = refresh_token(refreshable_token, client_id, client_secret, url)

        recently_played = get_recently_played(token, timestamp)

        timestamp = get_after_timestamp(recently_played, timestamp)

        save_data(recently_played)

        time.sleep(3600)

   
def main():

    client_id = credentials.client_id

    client_secret = credentials.client_secret

    redirect_uri = credentials.redirect_uri

    url = "https://accounts.spotify.com/api/token"

    timestamp = ""

    try:
        code = credentials.code
    except:
        code = ""

    try:
        refreshable_token = credentials.refreshable_token
    except:
        refreshable_token = ""  

    if code == "":

        code = get_code(redirect_uri, client_id)

    if refreshable_token == "":

        refreshable_token = get_refreshable_token(code, url)

    get_data(refreshable_token, client_id, client_secret, url, timestamp)



if __name__ == "__main__":

    main()

