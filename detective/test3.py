# -*- coding: utf-8 -*-
# import urllib.request
# stream_url = r'http://buyung.es.kr/sidopds.brd/_1.217.1ad4da65/네잎%20클로버.mp3'
# target_path = r'D:\★사용자 폴더\Downloads\네잎클로버_MR.mp3'
# urllib.request.urlretrieve(stream_url, target_path)

import requests


def download_file(url):
    local_filename = url.split('/')[-1]
    # local_filename = r'D:\★사용자 폴더\Downloads'
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                #f.flush() commented by recommendation from J.F.Sebastian
    return local_filename

if __name__=='__main__':
    download_file("http://buyung.es.kr/sidopds.brd/_1.217.1b7bdef8/%EB%84%A4%EC%9E%8E%20%ED%81%B4%EB%A1%9C%EB%B2%84.mp3")
