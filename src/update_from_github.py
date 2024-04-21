# This code has been adapted from https://github.com/RangerDigital/senko, full credit goes to
# Jakub Bednarski for the original functionality. I've merely hacked at it for my purposes!

import os
import gc
from lib import mrequests
from logger import publish_log_message

class Updater:
    def __init__(self, username, repository, client, ref="main", api_token=None):
        self.api_repository_contents_url = 'https://api.github.com/repos/{}/{}/contents/src?ref={}'.format(username, repository, ref)
        self.api_commits_url = 'https://api.github.com/repos/{}/{}/commits?per_page=1&sha={}'.format(username, repository, ref)
        self.headers = {
            b"User-Agent": '{}'.format(username)
        }

        if api_token is not None:
            self.headers[b'Authorization'] = 'token {}'.format(api_token)

        self.client = client

    async def _get_repository_contents(self, api_repository_contents_url):
        await publish_log_message(message={'message': 'Getting repository contents from {}'.format(api_repository_contents_url)}, client=self.client)

        gc.collect()

        response = mrequests.get(api_repository_contents_url, headers=self.headers)

        if response.status_code == 200:
            json = response.json()
            response.close()

            gc.collect()

            for file in json:
                await self._process_item(file)
        else:
            publish_log_message(message={'error': 'Failed to get repository contents, status code was {}'.format(response.status_code)}, client=self.client)
            response.close()

            gc.collect()



    async def _process_item(self, file):
        if file['type'] == 'file':
            await self._get_file(file['download_url'], file['name'])

        if file['type'] == 'dir':
            await self._get_dir(file['url'], file['name'])



    async def _get_file(self, url, filename):
        gc.collect()

        await publish_log_message(message={
            'message': 'Fetching {}'.format(url),
            'mem_free': gc.mem_free(),
            }, client=self.client)

        gc.collect()

        buf = bytearray(1024)

        response = mrequests.get(url, headers=self.headers)

        gc.collect()

        if response.status_code == 200:
            gc.collect()

            response.save(filename, buf=buf)

            gc.collect()

            await publish_log_message(message={
                'message': 'Sucessfully saved {}'.format(filename),
                'mem_free': gc.mem_free(),
                }, client=self.client)

            gc.collect()

        else:
            await publish_log_message(message={'error': 'Failed to get {}, status code was {}'.format(filename, response.status_code)}, client=self.client)

        response.close()
        gc.collect()



    async def _get_dir(self, url, dir_name):
        await publish_log_message(message={'message': 'Getting directory {}'.format(dir_name)}, client=self.client)

        gc.collect()

        response = mrequests.get(url, headers=self.headers)
        json = response.json()
        response.close()

        gc.collect()

        try:
            os.mkdir(dir_name)
        except:
            pass

        os.chdir(dir_name)

        for file in json:
            await self._process_item(file)

        os.chdir('..')



    async def _write_version_file(self, api_commits_url):
        await publish_log_message(message={'message': 'Getting latest commit hash...'}, client=self.client)

        gc.collect()

        response = mrequests.get(api_commits_url, headers=self.headers)
        json = response.json()
        response.close()

        gc.collect()

        commit_hash = json[0]['sha'][0:7]

        gc.collect()

        await publish_log_message(message={'message': 'Latest commit hash is {}, writing to .version file...'.format(commit_hash)}, client=self.client)

        with open('.version', 'w') as file:
            file.write(commit_hash)



    async def update(self):
        await self._get_repository_contents(self.api_repository_contents_url)
        await self._write_version_file(self.api_commits_url)
