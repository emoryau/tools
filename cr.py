import subprocess
import pyperclip
import os
import re
import webbrowser
import argparse

jira_server = 'https://localedge.atlassian.net'
collab_server= 'http://collaborator.localedge.com'
username = 'emory.au'
password = 'Jaguar8675309*'

#Argument Parsing
parser = argparse.ArgumentParser(description="Code Collaborator review generator")
parser.add_argument('-r', '--revisions', help='Hashcode revisions to use for diff', required=False, type=str)
parser.add_argument('-i', '--id', help='Specify code review id (for updating existing reviews)', required=False, type=str)
parser.add_argument('-m', '--allow-modified', action='store_true', help='Skip check for modifications that have not been checked in')
parser.add_argument('-1', '--last', help="diff last revision only", required=False)
args = parser.parse_args()

def get_diff_arg_string():
    if args.last is not None:
        revision_hash = '-2:-1'
    elif args.revisions is None:
        hg_pipe = subprocess.Popen(['hg', 'id', '-i', '-r', 'parents(min(branch(.)))'], stdout=subprocess.PIPE)
        starting_hash = hg_pipe.stdout.read().decode('utf-8').rstrip('\r\n')

        hg_pipe = subprocess.Popen(['hg', 'id', '-i'], stdout=subprocess.PIPE)
        ending_hash = hg_pipe.stdout.read().decode('utf-8').rstrip('\r\n')

        revision_hash = str.format('{}:{}', starting_hash, ending_hash)
    else:
        revision_hash = args.revisions

    return str.format('-w -r {}', revision_hash), revision_hash

def get_branchname():
    # extract from HG branch / command line / UI
    hg_pipe = subprocess.Popen(['hg', 'branch'], stdout=subprocess.PIPE)
    branchname = hg_pipe.stdout.read().decode('utf-8').rstrip('\r\n')
    return branchname

def get_component_name():
    component = os.path.relpath('.', '..')
    return component

def print_diff(revision_hash):
    hg_pipe = subprocess.Popen(['hg', 'diff', '-w', '-B', '-r', revision_hash], stdout=subprocess.PIPE)
    diff_output = hg_pipe.stdout.read().decode('utf-8')

    print(diff_output)

def ConstructJiraLink(issue_key):
    return jira_server + '/browse/' + issue_key

def construct_ccollab_link(review_id):
    return collab_server + str.format('/ui#review:id={}', review_id)
    
diff_arg_string, revision_hash = get_diff_arg_string()
review_name = str.format('{}: {}', get_branchname(), get_component_name())

print(diff_arg_string)
print(review_name)
pyperclip.copy(diff_arg_string)

try:
    review_id = 0
    if args.id is None:
        out = subprocess.check_output(['ccollab.exe', '--no-browser', '--password', password, 'admin', 'review', 'create', '--title', review_name, '--custom-field', 'Jira issue link=%s' % (ConstructJiraLink(get_branchname()))])
        review_regex = re.compile(r"review (\d*)\.")
        review_id = review_regex.search(out.decode('UTF-8')).group(1)
        subprocess.check_output(['ccollab.exe', '--password', password, 'admin', 'review', 'participant', 'assign', review_id, username, 'Author'])
    else:
        review_id = args.id
    print(str.format('ccollab.exe --no-browser --password {} addhgdiffs {} -w -B -r {}', password, review_id, revision_hash))
    subprocess.check_output(['ccollab.exe', '--no-browser', '--password', password, 'addhgdiffs', review_id, '-w', '-B', '-r', revision_hash])

except subprocess.CalledProcessError as e:
    print (e)
    exit(1)

review_link = construct_ccollab_link(review_id)
print(review_link)
print('Link copied to clipboard')
pyperclip.copy(str.format('{}: {}\n', get_component_name(), review_link))
webbrowser.open_new_tab(review_link)
