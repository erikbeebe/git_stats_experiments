## This is terrible, no one should use this for anything -- erik

from pprint import pprint
import requests
import sys
import time

### configurables
user            = 'LOGIN'
password        = 'PASSWORD'
org             = 'YOUR_ORG'
repos_to_ignore = [] ## add names you don't want in the report here

repos = []
totals = {}

## add retry logic since github returns 202 if it's not in cache
def smart_get(org, repo, stat):
    ## commit_activity or code_frequency
    retry_counter = 0
    retry_max = 10

    while retry_counter < retry_max:
        retry_counter += 1
        r = requests.get('https://api.github.com/repos/%s/%s/stats/%s' % (org, repo, stat), auth=(user, password))
        if r.status_code == 202:
            print "Repo %s/%s not in cache, retrying %s more times before giving up.." % (org, repo, (retry_max-retry_counter))
            time.sleep(2)
        elif r.status_code == 200:
            ## looks good, assuming reasonable json
            print "Repo %s/%s (%s) found in cache, all good.." % (org, repo, stat)
            return r.json()
        else:
            print "Some other bad status while querying for %s/%s" % (org, repo)
            raise

    ## giving up
    print "Unknown status code returned, exiting.. probably try running it again, or check creds"
    sys.exit(1)

def get_repos():
    r = requests.get('https://api.github.com/orgs/%s/repos' % org, auth=(user, password))
    if r.status_code != 200:
        print "Unable to get repo list from Github - probably an auth problem.  HTTP status was %s, giving up" % r.status_code
        sys.exit(1)

    for repo in r.json():
        repos.append(repo['name'])

    for x in repos_to_ignore:
        if x in repos:
            repos.remove(x)

def get_activity():
    for repo in repos:
        ## commit activity
        j = smart_get(org, repo, "commit_activity")

        total = 0
        for x in j: total += x['total']

        ## code frequency
        j = smart_get(org, repo, "code_frequency")
  
        adds = 0
        deletes = 0

        for x in j: adds += x[1]
        for x in j: deletes += x[2]
 
        totals[repo] = [total, adds, deletes]
        
def print_activity():
    print "\n%s Activity, last 52 weeks" % org
    print "-" * 75
    print "%-40s %-10s %-10s %-10s" % ("Repository", "Commits", "Added", "Deleted")
    print "-" * 75

    total_commits_all_repos = 0
    total_adds_all_repos = 0
    total_deletes_all_repos = 0

    for repo in totals:
        print "%-40s %-10s %-10s %-10s" % (repo, totals[repo][0], totals[repo][1], totals[repo][2])
        total_commits_all_repos += totals[repo][0]
        total_adds_all_repos += totals[repo][1]
        total_deletes_all_repos += totals[repo][2]

    print "\nTotal commits for the last 52 weeks: %s" % total_commits_all_repos
    print "Total lines added for the last 52 weeks: %s" % total_adds_all_repos
    print "Total lines deleted for the last 52 weeks: %s" % total_deletes_all_repos
    print "Delta code added: %s" % (int(total_adds_all_repos) + int(total_deletes_all_repos))

if __name__ == "__main__":
    ## populate repos list
    get_repos()
    ## build totals dictionary
    get_activity()
    ## pretty print report
    print_activity()
