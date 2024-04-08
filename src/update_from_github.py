# This code has been adapted from https://github.com/RangerDigital/senko, full credit goes to
# Jakub Bednarski for the original functionality. I've merely hacked at it for my purposes!

import os
import gc
import urequests
from logger import publish_log_message

class UpdateFromGitHub:
    def __init__(self, username, repository, client, ref="main", api_token=None):
        self.api_url = "https://api.github.com/repos/{}/{}/contents/src?ref={}".format(username, repository, ref)
        self.headers = {
            "User-Agent": username
        }

        if api_token is not None:
            self.headers.append({"Authorization": "token %s" % api_token})

        self.client = client

    async def _get_repository_contents(self, api_url):
        await publish_log_message(message={'message': f'Getting repository contents from {api_url}'}, client=self.client)

        response = urequests.get(api_url, headers=self.headers)
        json = response.json()

        for file in json:
            await self._process_item(file)

    async def _process_item(self, file):
        if file['type'] == 'file':
            await self._get_file(file['download_url'], file['name'])

        if file['type'] == 'dir':
            await self._get_dir(file['url'], file['name'])

    async def _get_file(self, url, filename):
        gc.collect()

        await publish_log_message(message={'message': f'Fetching {url}'}, client=self.client)

        response = urequests.get(url, headers=self.headers)
        code = response.status_code

        if code == 200:
            with open(filename, "w") as local_file:
                local_file.write(response.text)
        else:
            await publish_log_message(message={'error': f'Failed to get {filename}, status code was {code}'}, client=self.client)

    async def _get_dir(self, url, dir_name):
        await publish_log_message(message={'message': f'Getting directory {dir_name}'}, client=self.client)

        response = urequests.get(url, headers=self.headers)
        json = response.json()

        try:
            os.mkdir(dir_name)
        except:
            pass

        os.chdir(dir_name)

        for file in json:
            await self._process_item(file)

        os.chdir('..')

    async def update(self):
        await self._get_repository_contents(self.api_url)
