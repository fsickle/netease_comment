
import requests
import json
import os
import base64
import codecs
from Crypto.Cipher import AES


class Netease():

    first_data = {"rid": "R_SO_4_520400044", "offset": "0", "total": "true", "limit": "20", "csrf_token": ""}
    second_data = '010001'
    third_data = '00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e41762' \
                 '9ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b4' \
                 '24d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7'
    fourth_data = '0CoJUm6Qyw8W8jud'

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

    def get_comment(self, data):
        music_id = "520400044"
        comment_url = "https://music.163.com/weapi/v1/resource/comments/R_SO_4_" + music_id + "?csrf_token="
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.75'
                          ' Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        form_data = data
        content = requests.post(url=comment_url, data=form_data, headers=headers)
        comments = json.loads(content.text)
        result = dict()
        if comments:
            for i in range(15):
                text = comments["hotComments"][i]["content"]
                result[i] = text
            total = comments["total"]
            result["total"] = total
            print(result)

    def main(self):
        data = self.encrypted_request(self.first_data, self.second_data, self.third_data, self.fourth_data)
        self.get_comment(data)


if __name__ == '__main__':
    s = Netease()
    s.main()