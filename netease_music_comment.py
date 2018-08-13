
import requests
import json
import os
import base64
import codecs
from Crypto.Cipher import AES
import pymongo
from pyquery import PyQuery as pq
import re
import time
import random


count = 0


class Netease():

    def __init__(self):
        self.proxyHost = "http-dyn.abuyun.com"
        self.proxyPort = "9020"
        self.proxyUser = ''
        self.proxyPass = ''

        self.proxyMeta = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
            "host": self.proxyHost,
            "port": self.proxyPort,
            "user": self.proxyUser,
            "pass": self.proxyPass,
        }
        self.proxies = {
            "http": self.proxyMeta,
            "https": self.proxyMeta,
        }
        self.second_data = '010001'
        self.third_data = '00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76' \
                          'd2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee25' \
                          '5932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7'
        self.fourth_data = '0CoJUm6Qyw8W8jud'
        self.mongo_uri = 'localhost'
        self.mongo_db = 'netease'
        self.collection = 'comments'
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        self.db['comments'].create_index('url', unique=True)

    def createSecretKey(self, size):
        '''获取随机十六个字母拼成的字符串'''
        '''
        os.urandom(n):产生n个字节的字符串
        ord(n):返回对应的十进制整数
        hex():将十进制整数转换成16进制，以字符串表示
        '''
        return (''.join(map(lambda x: (hex(ord(x))[2:]), str(os.urandom(size)))))[0:16]

    def aesEncrypt(self, text, secKey):
        '''encText加密方法:AES'''
        '''
        chr():以整数做参数，返回字符
        '''
        pad = 16 - len(text) % 16
        if isinstance(text, bytes):
            text = text.decode('utf-8')
        text = text + str(pad * chr(pad))
        encryptor = AES.new(secKey, AES.MODE_CBC, '0102030405060708')
        ciphertext = encryptor.encrypt(text)
        ciphertext = base64.b64encode(ciphertext)
        return ciphertext

    def rsaEncrypt(self, secKey, pubKey, modulus):
        '''encSecKey的加密方法:rsa'''
        text = secKey[::-1]
        rs = int(codecs.encode(text.encode('utf-8'), 'hex_codec'), 16) ** int(pubKey, 16) % int(modulus, 16)
        return format(rs, 'x').zfill(256)

    def encrypted_request(self, text, pubKey, modulus, nonce):
        text = json.dumps(text)
        secKey = self.createSecretKey(16)
        encText = self.aesEncrypt(self.aesEncrypt(text, nonce), secKey)
        encSecKey = self.rsaEncrypt(secKey, pubKey, modulus)
        data = {
            'params': encText,
            'encSecKey': encSecKey,
        }
        return data

    def get_first_data(self, url):
        music_id = re.search('id=(.*)', url).group(1)
        rid = "R_SO_4_" + music_id
        first_data = {"rid": rid, "offset": "0", "total": "true", "limit": "20", "csrf_token": ""}
        # print(first_data)
        return first_data

    def get_comment(self, data, url, name):
        music_id = re.search('id=(.*)', url) .group(1)
        comment_url = "https://music.163.com/weapi/v1/resource/comments/R_SO_4_" + music_id + "?csrf_token="
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.75'
                          ' Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        form_data = data
        time.sleep(0.25)
        content = requests.post(url=comment_url, data=form_data, headers=headers, timeout=2, proxies=self.proxies)
        comments = json.loads(content.text)
        length = len(comments["hotComments"])
        # print(length)
        result = dict()
        if length>0:
            for i in range(length):
                text = comments["hotComments"][i]["content"]
                result[str(i)] = text
            result['music_name'] = name
            total = comments["total"]
            result["total"] = str(total)
            result['url'] = url
            # print(result)
            return result
        else:
            result['music_name'] = name
            total = comments["total"]
            result["total"] = str(total)
            result['url'] = url
            result['0'] = 'No Comment'
            return result

    def get_name(self, url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.75Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Referer': 'https://music.163.com/',
            'Host': 'music.163.com'
        }
        print(url)
        time.sleep(0.25)
        response = requests.get(url, headers=headers, timeout=2)
        doc = pq(response.text)
        name = re.search('"title": "(.*?)",', response.text).group(1)
        urls = list()
        url = doc('div.g-bd4.f-cb div.g-sd4 div ul.m-sglist.f-cb li.f-cb div.txt div.f-thide:first-child a')
        for i in url.items():
            url = 'https://music.163.com' + i.attr('href')
            urls.append(url)
        n = random.randint(2, len(urls))
        list_url = urls[n-1]
        # print(urls)
        # list_urls = list()
        # list_url = doc('div.g-bd4.f-cb div.g-sd4 div ul.m-rctlist.f-cb li div.info p.f-thide a')
        # for i in list_url.items():
        #     url = 'https://music.163.com' + i.attr('href')
        #     list_urls.append(url)
        # # print(list_urls)
        return name, list_url

    def get_list(self, list_url, from_url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.75Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Referer': 'https://music.163.com/',
            'Host': 'music.163.com'
        }
        time.sleep(0.25)
        response = requests.get(list_url, headers=headers, timeout=2)
        doc = pq(response.text)
        urls = list()
        song_urls = doc('div#song-list-pre-cache ul.f-hide li a')
        for i in song_urls.items():
            url = 'https://music.163.com' + i.attr('href')
            urls.append(url)
        urls.remove(from_url)
        # print(urls)
        return urls

    def save_mongodb(self, result):
        try:
            self.db['comments'].insert_one(result)
            print('存储到MongoDB', result)
            return True
        except pymongo.errors.DuplicateKeyError as e:
            print('错误为', e)
            count = self.count()
            if count>100:
                print('下载重复歌曲100次')
                return False
        return True

    def count(self):
        global count
        count += 1
        return count

    def main(self, url):
        # for url in urls:
        name, list_urls = self.get_name(url)
        first_data = self.get_first_data(url)
        data = self.encrypted_request(first_data, self.second_data, self.third_data, self.fourth_data)
        result = self.get_comment(data, url, name)
        self.save_mongodb(result)
        # for list_url in list_urls:
        #     new_urls = self.get_list(list_url, url)
        #     self.main(new_urls)
        self.main(list_urls)
            # print(new_urls)
            # self.main(new_urls)


if __name__ == '__main__':
    start_url = 'https://music.163.com/song?id=63650'
    s = Netease()
    s.main(start_url)