from urllib.parse import urlparse
import requests
import json
from pprint import pprint
from time import sleep
from waybackpy import WaybackMachineCDXServerAPI
from bs4 import BeautifulSoup

#"https://plays.tv/u/meffhed" "https://plays.tv/u/MrNicola", 
urls = ["https://plays.tv/u/QUonan"]

waybackdata = []
library = []


parsed = urlparse("https://web.archive.org/web/20191210164724/https://plays.tv/video/5b11c7b45f556f0942/sexy-man?from=user&_t=eyJ0eXBlIjoiZnJvbSIsImxvY2F0aW9uIjoiUmVwbGF5VXNlckNvbnRyb2xsZXIuVXNlclZpZGVvc01vZC12aWRlb3MiLCJmZWVkX2lkIjoiNWIxMWM3YjQ1ZjU1NmYwOTQyIiwiZ2FtZV9pZCI6IjA0MDk0YmYxZjE2MjU5NGIyODcwN2I1MGM0ZTgzNDllIiwibGlua19pZCI6InZpZGVvX2xpc3RfdGh1bWIifQ%3D%3D")

for url in urls:
    save_api = WaybackMachineCDXServerAPI(url)
    user = url.split('/')[-1]

    pprint(f"getting urls for {user}")

    near = save_api.near(year=2019, month=10, day=10, hour=17, minute=17, )
    
    response = requests.get(near.archive_url)

    soup = BeautifulSoup(response.content, "html.parser")

    video_div = soup.find("div", {"id": "B"})

    if video_div is None:
        print(f"no videos found for {user}")
        continue

    video_items = video_div.findAll("li", {"class": "video-item"})

    if len(video_items) < 1:
        print(f"no videos found for {user}")
        continue

    for video in video_items:
        try:
            vid_info = video.find("")
        except:
            pass
    

    data = [
        json.loads(x.string) for x in soup.find_all("script", type="application/ld+json")
    ]
    waybackdata.append({
        'user': user,
        'data': data[0]['video'],
        'videos': []
    })



pprint(waybackdata)

# newobj = {
#         "name": d["name"],
#         "url": d["embedURL"],
#         "url_content": requests.get(d["embedURL"]).content
#     }

for user_data in waybackdata:
    data = user_data["data"]
    pprint(f"----Processing for {user_data['user']} (possible videos: {len(data)}) -------")



    for vid in data:
        title =  vid["name"]
        url = vid["embedURL"]
        pprint(f"processing vid {title} ({url})")
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        text_header = soup.find('h1')

        if  text_header is not None and text_header.next == 'Medal.tv':
            continue
        

        # <h1>Medal.tv</h1>
        
        try:
            vid_element = soup.find('source', {"res": "720"}).attrs["src"]
        except:
            try:
                vid_element = soup.find('source', {"res": "480"}).attrs["src"]
            except:
                continue
        
        
        vid_data = {
            "title": title,
            "video_url": vid_element
        }
        user_data["videos"].append(vid_data)
        pprint("waiting 3s")
        sleep(1)




pprint(waybackdata)

