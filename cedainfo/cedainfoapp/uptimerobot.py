#
# Contains routines for getting relevant data from uptimerobot.com
#
import http.client
import json

UPTIMEROBOT_API_KEY = "ur668013-4786377064a9ad449c09d1de"

def get_all_monitors():
    #
    # Returns all monitor information as an array of hashes. If there are more than 50 monitors then need to do it in two calls
    #
    data_page_1 = get_monitors(offset=0)
    total_monitor_count = data_page_1["pagination"]["total"]

    if total_monitor_count > 50:
        data_page_2 = get_monitors(offset=50)
        monitors = data_page_1["monitors"] + data_page_2["monitors"]
    else:
        monitors = data_page_1

    return monitors

def get_monitors(offset=0):
    #
    # Get chunk of monitor information using the given offset
    #
    conn = http.client.HTTPSConnection("api.uptimerobot.com")
    payload = f"api_key={UPTIMEROBOT_API_KEY}&format=json&logs=0&offset={offset}"

    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "cache-control": "no-cache",
    }

    conn.request("POST", "/v2/getMonitors", payload, headers)

    res = conn.getresponse()
    data = res.read()

    return json.loads(data.decode("utf-8"))

if (__name__ == '__main__'):
    all_monitors = get_all_monitors()
    all_monitors = sorted(all_monitors, key=lambda d: d["friendly_name"].lower())

    count = 1
    for monitor in all_monitors:
        print(count, monitor["id"], monitor["friendly_name"], monitor["url"])
        count = count + 1
