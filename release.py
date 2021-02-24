from jira import JIRA
import tkinter
import webbrowser
import xml.etree.ElementTree as ET
import subprocess
import argparse
import sys
import os

jira_server = 'https://localedge.atlassian.net'
jira_user = 'eau@localedge.com'
jira_token = 'fh3MuTo1fyLJ0Rair3uY3CFB'

component = os.path.relpath('.', '..').lower()

# Extract from POM
if (os.path.exists('pom.xml')):
    pom = ET.parse('pom.xml')
    nsmap = {'m': 'http://maven.apache.org/POM/4.0.0'}
    raw_version = pom.find('m:version',nsmap).text
    raw_group = pom.find('m:groupId', nsmap).text
    raw_artifact = pom.find('m:artifactId', nsmap).text

    maven_dependency = ('<dependency>\r\n'
                        '\t<groupId>' + raw_group + '</groupid>\r\n'
                        '\t<artifactId>' + raw_artifact + '</artifactId>\r\n'
                        '\t<version>' + raw_version + '</version>\r\n'
                        '</dependency>')
elif (os.path.exists('docker-image-version.txt')):
    # No maven dependency on this release ticket
    maven_dependency = ''

    # Try load version from file
    with open('docker-image-version.txt', 'r') as file:
        raw_version = file.read().replace('\n', '')
else:
    print('Could not find compatible version source')
    exit()

split_version = raw_version.split('.')
majorVersion = int(split_version[0])
minorVersion = int(split_version[1])
raw_patch = split_version[2].split('-')
patchVersion = int(raw_patch[0])
snapshot = ''
if len(raw_patch) > 1:
    snapshot = raw_patch[1]

# extract from HG branch / command line / UI
hg_pipe = subprocess.Popen(['hg', 'branch'], stdout=subprocess.PIPE)
branchname = hg_pipe.stdout.read().decode('utf-8').rstrip('\r\n')

if branchname != 'dev' and branchname != 'default':
    link = branchname
else:   
    link = ''
# extract from command line / UI / parent issue
parser = argparse.ArgumentParser(description='Create JIRA Release tickets')
parser.add_argument('description', help='description to use in Ticket')
args = parser.parse_args()
description = args.description


components = [{'name': component}]
version = str(majorVersion) + '.' + str(minorVersion) + '.' + str(patchVersion)
summary = component + ' ' + version

def AddLabel(root, name, text, height=1):
    container = tkinter.Frame(root)
    name_label = tkinter.Label(container, text=name, anchor=tkinter.E, width=25)
    text_label = tkinter.Text(container, height=height)
    text_label.insert(tkinter.INSERT, text)
    
    name_label.grid(column=0,row=0)
    text_label.grid(column=1,row=0)
    container.pack(fill=tkinter.X)
    return text_label

def CreateIssue():
    #Start JIRA
    jira_client = JIRA(server=jira_server, basic_auth=(jira_user, jira_token))

    issue_dict = {
        'project': 'REL',
        'issuetype': {'name': 'Release'},
        'summary': summary,
        'description': description,
        'components': components,
        'customfield_12100': majorVersion,
        'customfield_12101': minorVersion,
        'customfield_12102': patchVersion,
        'customfield_12104': maven_dependency,
    }
    new_issue = jira_client.create_issue(fields=issue_dict)
    print(new_issue.key)

    link = link_label.get('1.0', tkinter.END + '-1c')
    if link != '':
        for single_link in link.split('/'):
            jira_client.create_issue_link('Relates', new_issue.key, single_link)

    webbrowser.open_new_tab(ConstructJiraLink(new_issue.key))
    return new_issue

def ConstructJiraLink(issue_key):
    return jira_server + '/browse/' + issue_key

def OpenLink(event):
    link = link_label.get('1.0', tkinter.END + '-1c')
    webbrowser.open_new_tab(ConstructJiraLink(link))

# Commenting out TK for now, UI is more trouble than it's worth
root = tkinter.Tk()
root.title('JIRA Release Generator')

AddLabel(root, 'Summary', summary)
AddLabel(root, 'Version', version)
AddLabel(root, 'Description', description)
AddLabel(root, 'Component', component)
AddLabel(root, 'Maven Dependency', maven_dependency.replace('\r',''), 5)
link_label = AddLabel(root, 'Link', link)
link_label.bind('<Double-Button-1>', OpenLink)

# tkinter.Button(root, command=exit, text='Close').pack(side = tkinter.LEFT)
# tkinter.Button(root, command=CreateIssue, text='Create').pack(side = tkinter.RIGHT)
#
# root.mainloop()

CreateIssue();