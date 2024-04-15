# This code has been adapted from https://github.com/RangerDigital/senko, full credit goes to
# Jakub Bednarski for the original functionality. I've merely hacked at it for my purposes!

import os
import gc
import mrequests
from logger import publish_log_message

class Updater:
    def __init__(self, username, repository, client, ref="main", api_token=None):
        self.api_repository_contents_url = f'https://api.github.com/repos/{username}/{repository}/contents/src?ref={ref}'
        self.api_commits_url = f'https://api.github.com/repos/{username}/{repository}/commits?per_page=1&sha={ref}'
        self.headers = {
            "User-Agent": username
        }

        if api_token is not None:
            self.headers['Authorization'] = f'token {api_token}'

        self.client = client

    async def _get_latest_commit_hash(self, api_commits_url):
        await publish_log_message(message={'message': 'Getting latest commit hash...'}, client=self.client)

        gc.collect()

        response = mrequests.get(api_commits_url, headers=self.headers)
        json = response.json()
        response.close()

        commit_hash = json[0]['sha'][0:7]

        gc.collect()

        await publish_log_message(message={'message': f'Latest commit hash is {commit_hash}, writing to .version file...'}, client=self.client)

        with open('.version', 'w') as file:
            file.write(commit_hash[0:7])


    async def _get_repository_contents(self, api_repository_contents_url):
        await publish_log_message(message={'message': f'Getting repository contents from {api_repository_contents_url}'}, client=self.client)

        gc.collect()

        response = mrequests.get(api_repository_contents_url, headers=self.headers)
        json = response.json()
        response.close()

        gc.collect()

        for file in json:
            await self._process_item(file)

    async def _process_item(self, file):
        if file['type'] == 'file':
            await self._get_file(file['download_url'], file['name'])

        if file['type'] == 'dir':
            await self._get_dir(file['url'], file['name'])

    async def _get_file(self, url, filename):
        await publish_log_message(message={
            'message': f'Fetching {url}',
            'mem_free': gc.mem_free(),
            }, client=self.client)

        gc.collect()

        buf = bytearray(1024)

        response = mrequests.get(url, headers=self.headers)

        gc.collect()

        if response.status_code == 200:
            gc.collect()

            response.save(filename, buf=buf)
            await publish_log_message(message={
                'message': f'Sucessfully saved {filename}',
                'mem_free': gc.mem_free(),
                }, client=self.client)

        else:
            await publish_log_message(message={'error': f'Failed to get {filename}, status code was {response.status_code}'}, client=self.client)

        response.close()
        gc.collect()

    async def _get_dir(self, url, dir_name):
        await publish_log_message(message={'message': f'Getting directory {dir_name}'}, client=self.client)

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

    async def update(self):
        await self._get_latest_commit_hash(self.api_commits_url)
        await self._get_repository_contents(self.api_repository_contents_url)
