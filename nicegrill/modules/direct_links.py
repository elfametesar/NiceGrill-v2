# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.
#
""" Userbot module containing various sites direct links generators"""

from os import popen
import os
from random import choice
from uuid import uuid4
from bs4 import BeautifulSoup
from nicegrill import run, Message
from nicegrill.utils import humanize
from telethon import TelegramClient as Client

import re
import requests
import urllib.parse
import json

class DirectGen:

    @run(command="direct")
    async def direct_link_generator(message: Message, client: Client):
        """ direct links generator """
        await message.edit("<i>Processing...</i>")

        url = message.args
        
        if message.reply_to_text:
            url = message.reply_to_text.text
        
        if not url:
            await message.edit("<i>Usage: .direct >insert url here<</i>")
            return

        reply = ''
        links = re.findall(r'\bhttps?://.*\.\S+', url)

        if not links:
            await message.edit("<i>No links found!</i>")
            return

        for link in links:
            if 'drive.google.com' in link:
                reply += DirectGen.gdrive(link)
            elif 'mega.' in link:
                reply += DirectGen.mega_dl(link)
            elif 'yadi.sk' in link:
                reply += DirectGen.yandex_disk(link)
            elif 'mediafire.com' in link:
                reply += DirectGen.mediafire(link)
            elif 'sourceforge.net' in link:
                reply += DirectGen.sourceforge(link)
            elif 'osdn.net' in link:
                reply += DirectGen.osdn(link)
            elif 'github.com' in link:
                reply += DirectGen.github(link)
            elif 'androidfilehost.com' in link:
                reply += DirectGen.androidfilehost(link)
            else:
                reply += "<i>" + re.findall(r"\bhttps?://(.*?[^/]+)",
                                    link)[0] + 'is not supported</i>'

        await message.edit(reply)


    def gdrive(url: str) -> str:
        """ GDrive direct links generator """
        drive = 'https://drive.usercontent.google.com/download?id='
        try:
            link = re.findall(r'\bhttps?://drive\.google\.com\S+', url)[0]
        except IndexError:
            reply = "<code>No Google drive links found</code>\n"
            return reply
        file_id = ''
        reply = ''
        if link.find("view") != -1:
            file_id = link.split('/')[-2]
        elif link.find("open?id=") != -1:
            file_id = link.split("open?id=")[1].strip()
        elif link.find("uc?id=") != -1:
            file_id = link.split("uc?id=")[1].strip()
        drive += f'{file_id}&export=download&authuser=0&confirm=t&uuid={uuid4()}&at=APZUnTUqR9KNAsVypgBzMZNNlmdj%3A1717004771038'
        reply = f"<a href='{drive}'>Direct Download Link</a>\n"
        return reply


    def yandex_disk(url: str) -> str:
        """ Yandex.Disk direct links generator
        Based on https://github.com/wldhx/yadisk-direct"""
        reply = ''
        try:
            link = re.findall(r'\bhttps?://.*yadi\.sk\S+', url)[0]
        except IndexError:
            reply = "<code>No Yandex.Disk links found</code>\n"
            return reply
        api = 'https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key={}'
        try:
            dl_url = requests.get(api.format(link)).json()['href']
            name = dl_url.split('filename=')[1].split('&disposition')[0]
            reply += f'[{name}]({dl_url})\n'
        except KeyError:
            reply += '<code>Error: File not found / Download limit reached</code>\n'
            return reply
        return reply


    def mega_dl(url: str) -> str:
        """ MEGA.nz direct links generator
        Using https://gist.github.com/zanculmarktum/170b94764bd9a3da31078580ccea8d7e"""
        reply = ''
        try:
            link = re.findall(r'\bhttps?://.*mega.*\.nz\S+', url)[0]
        except IndexError:
            reply = "<code>No MEGA.nz links found</code>\n"
            return reply
        
        if not os.path.exists("megafetch.sh"):
            os.popen("curl https://gist.githubusercontent.com/zanculmarktum/170b94764bd9a3da31078580ccea8d7e/raw/1adfba71a69ef155c1180ab21e8fb6bead1a6c92/megafetch.sh -o megafetch.sh")

        command = f'bash megafetch.sh {link}'
        result = popen(command).read()
        link, name, _, _ = result.splitlines()
        reply += f'<a href="{link}">{name}</a>\n'
        return reply


    def mediafire(url: str) -> str:
        """ MediaFire direct links generator """
        try:
            link = re.findall(r'\bhttps?://.*mediafire\.com\S+', url)[0]
        except IndexError:
            reply = "<code>No MediaFire links found</code>\n"
            return reply
        reply = ''
        page = BeautifulSoup(requests.get(link).content, 'lxml')
        info = page.find('a', {'aria-label': 'Download file'})
        dl_url = info.get('href')
        size = re.findall(r'\(.*\)', info.text)[0]
        name = page.find('div', {'class': 'filename'}).text
        reply += f'<a href="{dl_url}">{name} {size}</a>\n'
        return reply


    def sourceforge(url: str) -> str:
        """ SourceForge direct links generator """
        try:
            link = re.findall(r'\bhttps?://.*sourceforge\.net\S+', url)[0]
        except IndexError:
            reply = "<code>No SourceForge links found</code>\n"
            return reply
        file_path = re.findall(r'files(.*)/download', link)[0]
        reply = f"<b>Mirrors for </b><i>{file_path.split('/')[-1]}</i>\n"
        project = re.findall(r'projects?/(.*?)/files', link)[0]
        mirrors = f'https://sourceforge.net/settings/mirror_choices?' \
            f'projectname={project}&filename={file_path}'
        page = BeautifulSoup(requests.get(mirrors).content, 'html.parser')
        info = page.find('ul', {'id': 'mirrorList'}).findAll('li')
        for mirror in info[1:]:
            name = re.findall(r'\((.*)\)', mirror.text.strip())[0]
            dl_url = f'https://{mirror["id"]}.dl.sourceforge.net/project/{project}/{file_path}'
            reply += f"<a href='{dl_url}'>{name}</a> "
        return reply


    def osdn(url: str) -> str:
        """ OSDN direct links generator """
        osdn_link = 'https://osdn.net'
        try:
            link = re.findall(r'\bhttps?://.*osdn\.net\S+', url)[0]
        except IndexError:
            reply = "<code>No OSDN links found</code>\n"
            return reply
        page = BeautifulSoup(
            requests.get(link, allow_redirects=True).content, 'lxml')
        info = page.find('a', {'class': 'mirror_link'})
        link = urllib.parse.unquote(osdn_link + info['href'])
        reply = f"<b>Mirrors for </b><i>{link.split('/')[-1]}</i>\n"
        mirrors = page.find('form', {'id': 'mirror-select-form'}).findAll('tr')
        for data in mirrors[1:]:
            mirror = data.find('input')['value']
            name = re.findall(r'\((.*)\)', data.findAll('td')[-1].text.strip())[0]
            dl_url = re.sub(r'm=(.*)&f', f'm={mirror}&f', link)
            reply += f"<a href='{dl_url}'>{name}</a> "
        return reply


    def github(url: str) -> str:
        """ GitHub direct links generator """
        try:
            link = re.findall(r'\bhttps?://.*github\.com.*releases\S+', url)[0]
        except IndexError:
            reply = "<code>No GitHub Releases links found</code>\n"
            return reply
        reply = ''
        dl_url = ''
        download = requests.get(url, stream=True, allow_redirects=False)
        try:
            dl_url = download.headers["location"]
        except KeyError:
            reply += "<code>Error: Can't extract the link</code>\n"
        name = link.split('/')[-1]
        reply += f"<a href='{dl_url}'>{name}</a> "
        return reply


    def androidfilehost(url: str) -> str:
        """ AFH direct links generator """
        try:
            link = re.findall(r'\bhttps?://.*androidfilehost.*fid.*\S+', url)[0]
        except IndexError:
            reply = "<code>No AFH links found</code>\n"
            return reply
        fid = re.findall(r'\?fid=(.*)', link)[0]
        session = requests.Session()
        user_agent = DirectGen.useragent()
        headers = {'user-agent': user_agent}
        res = session.get(link, headers=headers, allow_redirects=True)
        headers = {
            'origin': 'https://androidfilehost.com',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9',
            'user-agent': user_agent,
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'x-mod-sbb-ctype': 'xhr',
            'accept': '*/*',
            'referer': f'https://androidfilehost.com/?fid={fid}',
            'authority': 'androidfilehost.com',
            'x-requested-with': 'XMLHttpRequest',
        }
        data = {
            'submit': 'submit',
            'action': 'getdownloadmirrors',
            'fid': f'{fid}'
        }
        mirrors = None
        reply = ''
        error = "<code>Error: Can't find Mirrors for the link</code>\n"
        try:
            req = session.post(
                'https://androidfilehost.com/libs/otf/mirrors.otf.php',
                headers=headers,
                data=data,
                cookies=res.cookies)
            mirrors = req.json()['MIRRORS']
        except (json.decoder.JSONDecodeError, TypeError):
            reply += error
        if not mirrors:
            reply += error
            return reply
        for item in mirrors:
            name = item['name']
            dl_url = item['url']
            reply += f"<a href='{dl_url}'>{name}</a> "
        return reply


    def useragent():
        """
        useragent random setter
        useragents = BeautifulSoup(
            requests.get(
                'https://developers.whatismybrowser.com/'
                'useragents/explore/operating_system_name/android/').content,
            'lxml').findAll('td', {'class': 'useragent'})
        """
        user_agent = "Mozilla/5.0 (Linux; Android 9; SM-G960F Build/PPR1.180610.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.157 Mobile Safari/537.36"
        return user_agent
