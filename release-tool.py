#!/usr/bin/python

import json
import os
from optparse import OptionParser
import requests
import sys
import logging as log

__author__ = 'ravi'

API_URL = 'https://api.github.com/repos/{}/{}/releases'
UPLOAD_URL = 'https://github.com/api/uploads/repos/{}/{}/releases'


class GitHubRelease(object):
    def __init__(self, in_user, in_owner, in_repo, in_password='x-oauth-basic'):
        self.user = in_user
        self.password = in_password
        self.repo = in_repo
        self.url = API_URL.format(in_owner, in_repo)
        self.upload_url = UPLOAD_URL.format(in_owner, in_repo)

    def get_releases(self):
        releases_response = requests.get(self.url, auth=(self.user, self.password))
        if releases_response.status_code >= 400:
            print "Cannot retrieve releases from api. Reponse: %d" % releases_response.status_code
            return 
        return json.loads(releases_response.text)

    def create_release(self, tag, name=None, description=None, draft=False, prerelease=False):
        data = {
            "tag_name": tag,
            "target_commitish": "master",
            "name": name if name else tag,
            "body": description if description else tag,
            "draft": draft,
            "prerelease": prerelease
        }
        json_data = json.dumps(data)
        response = requests.post(self.url, data=json_data, auth=(self.user, self.password))
        json_response = json.loads(response.text)
        if json_response.get('errors') or json_response.get('message'):
            log.error(response.text)
            return False
        else:
            print("Successfully created release {} for {}".format(tag, self.repo))
            return True

    def find_id_for_tag(self, release_id):
        all_releases = self.get_releases()
        for release in all_releases:
            if release.get('tag_name') == release_id:
                return release.get('id')
        return None

    def delete_release(self, tag_name):
        release_id = self.find_id_for_tag(tag_name)
        if not release_id:
            log.error("Could not find release for tag name: {}".format(tag_name))
            return False
        response = requests.delete('{}/{}'.format(self.url, release_id),
                                   auth=(self.user, self.password))
        response.raise_for_status()
        print "Successfully deleted release {}".format(tag_name)
        return True


if __name__ == "__main__":
    parser = OptionParser(usage='usage: %prog [options] arguments', add_help_option=False)
    parser.add_option("-c", "--create", action="store_true", dest="create")
    parser.add_option("-d", "--delete", action="store_true", dest="delete")
    parser.add_option("-t", "--token", dest="git_hub_token")
    parser.add_option("-o", "--owner", dest="owner")
    parser.add_option("-r", "--repo", dest="repo")
    parser.add_option("-v", "--version", dest="version")
    (options, args) = parser.parse_args()
    if options.git_hub_token is None or options.owner is None or options.repo is None:
        parser.print_help()
        print ''
        print 'Example:'
        print 'github_releases.py -t 1234567890 -o simplymeasured -r immortal_wombat'
        sys.exit(-1)
    if options.create or options.delete and not options.version:
        parser.print_help()
        print ""
        print "Version is required when creating or deleting a release!"
        sys.exit(1)

    gh_release = GitHubRelease(options.git_hub_token, options.owner, options.repo)
    try:
        if options.create:
            result = gh_release.create_release("v{}".format(options.version))
        elif options.delete:
            try:
                result = gh_release.delete_release("v{}".format(options.version))
            except:
                pass
        else:
            result = gh_release.get_releases()

            print('Releases:')
            for release in result:
                print(release['name'] + " - " + release['body'])

        if result:
            sys.exit()
        else:
            sys.exit(-2)
    except Exception as exc:
        log.error(exc.message)
        sys.exit(-2)
