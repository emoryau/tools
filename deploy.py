import xml.etree.ElementTree as xml
import subprocess
import os
import webbrowser
import argparse
import shutil
from jira import JIRA
from prompt_toolkit import prompt
from prompt_toolkit.contrib.completers import WordCompleter
import datetime
import json
import pyperclip
from pyadf.document import Document
from pyadf.paragraph import Paragraph


# jira_server = 'https://emcomplete.atlassian.net'
# jira_user = 'emoryau@gmail.com'
# jira_token = 'O30SE83e4IcTl4lw2GTY2F8F'
jira_server = 'https://localedge.atlassian.net'
jira_user = 'eau@localedge.com'
jira_token = 'fh3MuTo1fyLJ0Rair3uY3CFB'
jira_account_id_me = '557058:b7f59859-6ada-41e7-a52f-fb857e8dd9f9'  # @localedge
jira_account_id_po = '557058:d6724e93-fbeb-4cc7-b374-513975bac670'  # glenn
#jira_account_mentions = ['557058:b7f59859-6ada-41e7-a52f-fb857e8dd9f9','557058:fe76b216-dd2b-4fb6-bfa9-898d83c6712f']  # localedge & personal
jira_account_mentions = ['557058:7e28aa77-6187-4569-9c14-bd90c7ae2272']  # mckane & justin

wiki_base = r''
hg_base = r'http://vcs.localedge.com/hg'
jenkins_base = r'http://jenkins.localedge.com'
deploy_folder_base = r'\\lebfs01.wdp1.white-directory.com\docs\IT_Product\DEV/Deployment\Java\Single-Build'
deploy_static_folder_base = r'file://lebfs01.wdp1.white-directory.com/docs/IT_Product/DEV/Deployment/Java'
dev_process_server = 'lecdazrps01'
qa_process_server = 'lecqazrps01'
stage_process_server = 'lecsazrps01'
prod_process_server = 'lecazrps01'
environments = dict()
environments['dev'] = dict(process_server='lecdazrps01', admin_name='DEV', server_environment='Development',
                           should_have_snapshot=True, static_dir='Development')
environments['qa'] = dict(process_server='lecqazrps01', admin_name='QA', server_environment='QA',
                          should_have_snapshot=True, static_dir='QA')
environments['stage'] = dict(process_server='lecsazrps01', admin_name='STAGING', server_environment='Staging',
                             should_have_snapshot=False, static_dir='Staging-UAT')
environments['prod'] = dict(process_server='lecazrps01', admin_name='PRODUCTION', server_environment='Production',
                            should_have_snapshot=False, static_dir='Production')


# Extract from POM
def extract_artifact_version(pom, nsmap, version_override):
    if (version_override != ''):
        raw_version = version_override
    elif (pom != None):
        raw_version = pom.find('m:version', nsmap).text
    elif (os.path.exists('docker-image-version.txt')):
        # Try load version from file
        with open('docker-image-version.txt', 'r') as file:
            raw_version = file.read().replace('\n', '')
    else:
        print('Could not find compatible version source')
        exit()

    split_version = raw_version.split('.')
    raw_patch = split_version[2].split('-')
    majorVersion = int(split_version[0])
    minorVersion = int(split_version[1])
    patchVersion = int(raw_patch[0])
    snapshot = ''
    if len(raw_patch) > 1:
        snapshot = raw_patch[1]
    return majorVersion, minorVersion, patchVersion, snapshot, raw_version


def extract_group_and_artifact(pom, nsmap):
    raw_group = pom.find('m:groupId', nsmap)
    raw_artifact = pom.find('m:artifactId', nsmap)
    return raw_group.text, raw_artifact.text


def extract_packaging(pom, nsmap):
    if (pom == None):
        return 'None'
    raw_packaging = pom.find('m:packaging', nsmap)
    return raw_packaging.text


def extract_url(pom, nsmap):
    raw_url = pom.find('m:url', nsmap)
    if raw_url != None:
        return raw_url.text
    else:
        return ''


def extract_hg_checksum():
    hg_pipe = subprocess.Popen(['hg', 'id', '-i'], stdout=subprocess.PIPE)
    hg_output = hg_pipe.stdout.read().decode('utf-8').rstrip('\r\n')
    return hg_output


def extract_hg_link():
    hg_checksum = extract_hg_checksum()
    return str.format('{}/{}/files/{}/', hg_base, component, hg_checksum.strip('+'))


def extract_hg_branchname():
    hg_pipe = subprocess.Popen(['hg', 'branch'], stdout=subprocess.PIPE)
    branchname = hg_pipe.stdout.read().decode('utf-8').rstrip('\r\n')

    if branchname != 'dev' and branchname != 'default':
        return branchname
    else:
        return ''



# Argument Parsing
parser = argparse.ArgumentParser(description='Create JIRA Deployment tickets')
parser.add_argument('-s', '--server', help=str.format('Server environment to use {}', list(environments.keys())),
                    action='append', required=True, type=str)
parser.add_argument('-w', '--wiki', help='Wiki article to link', dest='wiki_link', default='')
parser.add_argument('-a', '--additional-instructions', help='Additional instructions to specify', default='')
parser.add_argument('-j', '--jobid', help='Jenkins pipeline job id', dest='jenkins_job_id', default='')
parser.add_argument('-v', '--version', help='Artifact Version', dest='version_override', default='')
parser.add_argument('artifact', help='filename of artifact to deploy, or - to build site.zip')
args = parser.parse_args()

if (os.path.exists('pom.xml')):
    pom = xml.parse('pom.xml')
elif (os.path.exists('docker-image-version.txt')):
    pom = None
    # Try load version from file
    with open('docker-image-version.txt', 'r') as file:
        raw_version = file.read().replace('\n', '')
else:
    pom = None
nsmap = {'m': 'http://maven.apache.org/POM/4.0.0'}

component = os.path.relpath('.', '..')


def construct_wikitable_head(col1, col2):
    return str.format('||{}||{}||\n', col1, col2)


def construct_wikitable_row(col1, col2):
    if col2 == '':
        col2 = ' '
    return str.format('|{}|{}|\n', col1, col2)


def construct_jiralink(name, link):
    return str.format('[{}|{}]', name, link)


def construct_deploy_folder(component, version, environment):
    if static_content:
        return construct_static_deploy_folder(component, environment)
    else:
        return str.format(r'{}\{}\{}', deploy_folder_base, component, version)


def construct_static_deploy_folder(component, environment):
    date = datetime.date.today()
    return str.format(r'{}\{}\{}\{}', deploy_static_folder_base, environment, component, date)


def ConstructJiraLink(issue_key):
    if issue_key != '':
        return jira_server + '/browse/' + issue_key
    else:
        return ''


def CreateIssue(summary, description, link, server_environment, due_date, is_container):
    container_value = 'No'
    if is_container == True:
        container_value = 'Yes'

    issue_dict = {
        'project': 'DEPLOY',
        'issuetype': {'name': 'Deployment'},
        'summary': summary,
        'description': description,
        # 'customfield_11000': {'value': server_environment},
        # 'customfield_13707': {'value': container_value},
        # 'duedate': due_date.isoformat()
    }
    new_issue = jira_client.create_issue(fields=issue_dict)
    print(str.format('New issue created: {}', ConstructJiraLink(new_issue.key)))

    try:
        if link != '':
            jira_client.create_issue_link('Relates', new_issue.key, link)
    except Exception as e:
        print(str.format('Failed to link issue {} because:\n{}', link, e))

    try:
        if is_container:
            jira_client.assign_issue(new_issue.key, account_id=jira_account_id_me)
    except Exception as e:
        print(str.format('Failed to assign issue {} because:\n{}', link, e))

    webbrowser.open_new_tab(ConstructJiraLink(new_issue.key))

    return new_issue


def construct_cron_table(component, version, wiki_link, schedule, server, additional_configuration):
    if additional_configuration == '':
        additional_configuration = ' '
    hg_link = extract_hg_link()

    jdoc = Document() \
        .table() \
        .tablerow() \
        .tableheader().paragraph().text('Wiki Link').end().end() \
        .tablecell().paragraph().text('Confluence').link(wiki_link).end().end() \
        .end() \
        .tablerow() \
        .tableheader().paragraph().text('Version #').end().end() \
        .tablecell().paragraph().text(version).end().end() \
        .end() \
        .tablerow() \
        .tableheader().paragraph().text('Deployment Artifacts').end().end() \
        .tablecell().paragraph().text(construct_deploy_folder(component, version,
                                                              environments[args.server[0]]['static_dir'])).end().end() \
        .end() \
        .tablerow() \
        .tableheader().paragraph().text('Schedule').end().end() \
        .tablecell().paragraph().text(schedule).end().end() \
        .end() \
        .tablerow() \
        .tableheader().paragraph().text('Server').end().end() \
        .tablecell().paragraph().text(server).end().end() \
        .end() \
        .tablerow() \
        .tableheader().paragraph().text('Additional Configuration').end().end() \
        .tablecell().paragraph().text(additional_configuration).end().end() \
        .end() \
        .tablerow() \
        .tableheader().paragraph().text('VCS Revision').end().end() \
        .tablecell().paragraph().text(hg_link).link(hg_link).end().end() \
        .end() \
        .end() \
        .paragraph() \
        .text('FYI ') \
        .mention(mention_id=jira_account_mentions[0], mention_text=jira_account_mentions[0]) \
        .end() \
        .to_doc()

    return jdoc['body']


def construct_war_table(component, version, wiki_link, additional_configuration):
    if additional_configuration == '':
        additional_configuration = ' '
    hg_link = extract_hg_link()

    jdoc = Document() \
        .table() \
        .tablerow() \
        .tableheader().paragraph().text('Wiki Link').end().end() \
        .tablecell().paragraph().text('Confluence').link(wiki_link).end().end() \
        .end() \
        .tablerow() \
        .tableheader().paragraph().text('WAR').end().end() \
        .tablecell().paragraph().text(construct_deploy_folder(component, version,
                                                              environments[args.server[0]]['static_dir'])).end().end() \
        .end() \
        .tablerow() \
        .tableheader().paragraph().text('Version #').end().end() \
        .tablecell().paragraph().text(version).end().end() \
        .end() \
        .tablerow() \
        .tableheader().paragraph().text('Additional Configuration').end().end() \
        .tablecell().paragraph().text(additional_configuration).end().end() \
        .end() \
        .tablerow() \
        .tableheader().paragraph().text('VCS Revision').end().end() \
        .tablecell().paragraph().text(hg_link).link(hg_link).end().end() \
        .end() \
        .end() \
        .paragraph() \
        .text('FYI ') \
        .mention(mention_id=jira_account_mentions[0], mention_text=jira_account_mentions[0]) \
        .mention(mention_id=jira_account_mentions[1], mention_text=jira_account_mentions[1]) \
        .end() \
        .to_doc()

    return jdoc['body']


def construct_static_content_table(component, environment, additional_configuration):
    table = '{panel:title=Static Content Deployment|borderStyle=dashed|borderColor=#ccc|titleBGColor=#F7D6C1|bgColor=#FFFFCE}'
    table += construct_wikitable_head('', '')
    table += construct_wikitable_row('Zip File', construct_static_deploy_folder(component, environment))
    table += construct_wikitable_row('Additional Configuration', additional_configuration)
    table += construct_wikitable_row('Source Control Revision', str.format('[{}]', extract_hg_link()))
    table += '{panel}\n'
    table += 'FYI [~mmckane] [~justinmoore]'

    return table

def jira_mentions():
    p = Paragraph()
    for id in jira_account_mentions:
        node = node.mention(id)

    return node

def construct_pipeline_table(component, version, wiki_link, additional_configuration, jenkins_job_id):
    if additional_configuration == '':
        additional_configuration = ' '
    hg_link = extract_hg_link()

    jdoc = Document() \
        .table() \
            .tablerow() \
                .tableheader().paragraph().text('Docs').end().end() \
                .tablecell().paragraph().text('Confluence').link(wiki_link).end().end() \
            .end() \
            .tablerow() \
                .tableheader().paragraph().text('Pipeline').end().end() \
                .tablecell().paragraph().text('Jenkins').link(construct_pipeline_link(component, jenkins_job_id)).end().end() \
            .end() \
            .tablerow() \
                .tableheader().paragraph().text('Version #').end().end() \
                .tablecell().paragraph().text(version).end().end() \
            .end() \
            .tablerow() \
                .tableheader().paragraph().text('Additional Configuration').end().end() \
                .tablecell().paragraph().text(additional_configuration).end().end() \
            .end() \
            .tablerow() \
                .tableheader().paragraph().text('VCS Revision').end().end() \
                .tablecell().paragraph().text(hg_link).link(hg_link).end().end() \
            .end() \
        .end() \
        .paragraph() \
            .text('FYI ') \
            .mention(mention_id=jira_account_mentions[0], mention_text=jira_account_mentions[0]) \
            .mention(mention_id=jira_account_mentions[1], mention_text=jira_account_mentions[1]) \
        .end() \
        .to_doc()

    return jdoc['body']

def construct_pipeline_link(component, jenkins_job_id):
    return jenkins_base + '/job/' + component + '-pipeline/' + jenkins_job_id

def create_static_content_zip():
    os.system(' cd target & 7z a site.zip site & cd ..')

def copy_artifact(artifact_filename, component, version, environment):
    target_folder = construct_deploy_folder(component, version, environment)
    print(str.format('Copying {} to {}', artifact_filename, target_folder))
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
    shutil.copy(artifact_filename, target_folder)
    print(str.format('Copy complete'))


def check_snapshot(snapshot, environment):
    if environments[environment]['should_have_snapshot']:
        if snapshot == '':
            print(str.format('Server envionment {} should only receive SNAPSHOT version. Current version is {}',
                             environments[environment]['server_environment'], full_version))
            exit(1)
    else:  # not should_be_snapshot
        if snapshot != '':
            print(str.format('Server envionment {} should only receive non-SNAPSHOT version. Current version is {}',
                             environments[environment]['server_environment'], full_version))
            exit(1)


major_version, minor_version, patch_version, snapshot, full_version = extract_artifact_version(pom, nsmap, args.version_override)
packaging = extract_packaging(pom, nsmap)
branchname = extract_hg_branchname()
static_content = False

table = 'ERROR'
for server_arg in args.server[:]:
    if str.lower(server_arg) in environments:
        server = environments[server_arg]['process_server']
        if str.lower(packaging) not in ['pom']:
            check_snapshot(snapshot, server_arg)
    else:
        print(str.format('Invalid server environment given. Available environments: {}', list(environments.keys())))
        exit(1)

due_date = datetime.datetime.today()
if 'prod' in args.server:
    # Calculate date
    if due_date.weekday() >= 1:
        due_date += datetime.timedelta(days=(8 - due_date.weekday()))
    else:
        due_date += datetime.timedelta(days=1)

is_container = False

# Detect static content
if component == 'static-content':
    static_content = True

if args.wiki_link == '':
    wiki_link = extract_url(pom, nsmap)
    if wiki_link == '' and not static_content:
        print(str.format('You must include <url> tag in pom or specify -w wiki link in command'))
        exit(1)
else:
    wiki_link = args.wiki_link

if static_content:
    table = construct_static_content_table(component, environments[args.server[0]]['static_dir'],
                                           args.additional_instructions)
elif args.jenkins_job_id != '':
    table = construct_pipeline_table(component, full_version, wiki_link, args.additional_instructions, args.jenkins_job_id)
elif str.lower(packaging) == 'war':
    table = construct_war_table(component, full_version, wiki_link, args.additional_instructions)
    is_container = True
elif str.lower(packaging) == 'jar':
    table = construct_cron_table(component, full_version, wiki_link, '(unchanged)', server,
                                 args.additional_instructions)

# Start JIRA
jira_client = JIRA(server=jira_server, basic_auth=(jira_user, jira_token), options={'rest_api_version': 3})

if (args.jenkins_job_id != ''):
    # pipeline tasks do not have a copy step
    commands = ['skip-copy', 'exit']
else:
    commands = ['create', 'skip-copy', 'exit']
CommandCompleter = WordCompleter(commands, ignore_case=True)

print('\n')
print(table)
print('\n')

# TODO remove this debugging stuff to re-enable normal operation
pyperclip.copy(json.dumps(table))
# exit()

while 1:
    print(str.format('Commands: {}', commands))
    user_input = prompt('>', completer=CommandCompleter).lower()

    if user_input == '' or user_input == 'exit':
        exit()

    if user_input == 'create':
        if static_content and args.artifact == '-':
            create_static_content_zip()
            args.artifact='target\\site.zip'
        copy_artifact(args.artifact, component, full_version, environments[args.server[0]]['static_dir'])

    # Create Deployment Ticket
    if user_input == 'create' or user_input == 'skip-copy':
        for server_arg in args.server[:]:
            summary = str.format('Please deploy {} to {}', component, environments[server_arg]['admin_name']);
            description = table

            print(summary)
            print(description)

            deploy_issue = CreateIssue(summary, description, branchname, environments[server_arg]['server_environment'],
                                       due_date, is_container)

        exit()
