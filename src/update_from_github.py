import urequests
import os
import gc

class UpdateFromGitHub:
    def __init__(self, username, repository, api_token=None, ref="main", working_dir="src"):
        """UpdateFromGitHub agent class.

        Args:
            username (str): GitHub username.
            repository (str): GitHub repository to fetch.
            api_token (str): GitHub API token to allow read access to private repositories. (None)
            ref (str): GitHub repository branch, commit, or tag to pull. (main)
            working_dir (str): Directory inside GitHub repo where the MicroPython app is. (src)
        """
        self.api_url = "https://api.github.com/repos/{}/{}/contents/{}?ref={}".format(username, repository, working_dir, ref)
        self.headers = {
            "User-Agent": username
        }
        if api_token is not None:
            self.headers.append({"Authorization": "token %s" % api_token})
        self.working_dir = working_dir

    def _get_repository_contents(self, api_url):
        response = urequests.get(api_url, headers=self.headers)
        json = response.json()

        for file in json:
            self._process_item(file)

    def _process_item(self, file):
        if file['type'] is 'file':
            self._get_file(file['download_url'], file['name'])

        if file['type'] is 'dir':
            self._get_dir(file['url'], file['name'])

    def _get_file(self, url, filename):
        gc.collect()

        print("Getting file %s" % url)

        response = urequests.get(url, headers=self.headers)
        code = response.status_code

        if code == 200:
            with open(filename, "w") as local_file:
                local_file.write(response.text)
        else:
            print("Failed to get file with status code " + code)

    def _get_dir(self, url, dir_name):
        print("Getting directory %s" % dir_name)

        response = urequests.get(url, headers=self.headers)
        json = response.json()

        try:
            os.mkdir(dir_name)
        except:
            pass

        os.chdir(dir_name)

        for file in json:
            self._process_item(file)

        os.chdir('..')

    def update(self):
        """Starts the process of pulling down the repository contents.

        Returns:
            None.
        """
        self._get_repository_contents(self.api_url)
