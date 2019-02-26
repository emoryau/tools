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

jira_server = 'https://localedge.atlassian.net'
wiki_base = r'http://localedge.atlassian.com/wiki'
hg_base = r'http://vcs.localedge.com/hg'
deploy_folder_base = r'\\LEBFS02\IT_Product\DEV\Deployment\Java\Single-Build'
deploy_static_folder_base = r'\\LEBFS02\IT_Product\DEV\Deployment\Java'
dev_process_server = 'lecdazrps01'
qa_process_server = 'lecqazrps01'
stage_process_server = 'lecsazrps01'
prod_process_server = 'lecawsps01'
environments = dict()
environments['dev'] = dict(process_server='lecdazrps01', admin_name='DEV', server_environment='Development',
                           should_have_snapshot=True, static_dir='Development')
environments['qa'] = dict(process_server='lecqazrps01', admin_name='QA', server_environment='QA',
                          should_have_snapshot=True, static_dir='QA')
environments['stage'] = dict(process_server='lecsazrps01', admin_name='STAGING', server_environment='Staging',
                             should_have_snapshot=False, static_dir='Staging-UAT')
environments['prod'] = dict(process_server='lecawsps01', admin_name='PRODUCTION', server_environment='Production',
                            should_have_snapshot=False, static_dir='Production')


# Extract from POM
def extract_artifact_version(pom, nsmap):
    raw_version = pom.find('m:version', nsmap)
    split_version = raw_version.text.split('.')
    raw_patch = split_version[2].split('-')
    majorVersion = int(split_version[0])
    minorVersion = int(split_version[1])
    patchVersion = int(raw_patch[0])
    snapshot = ''
    if len(raw_patch) > 1:
        snapshot = raw_patch[1]
    return majorVersion, minorVersion, patchVersion, snapshot, raw_version.text


def extract_group_and_artifact(pom, nsmap):
    raw_group = pom.find('m:groupId', nsmap)
    raw_artifact = pom.find('m:artifactId', nsmap)
    return raw_group.text, raw_artifact.text


def extract_packaging(pom, nsmap):
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
parser.add_argument('artifact', help='filename of artifact to deploy')
args = parser.parse_args()
print(args.server)

pom = xml.parse('pom.xml')
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


def CreateIssue(summary, description, link, server_environment, due_date):
    issue_dict = {
        'project': 'DEPLOY',
        'issuetype': {'name': 'Deployment'},
        'summary': summary,
        'description': description,
        'customfield_11000': {'value': server_environment},
        'duedate': due_date.isoformat()
    }
    new_issue = jira_client.create_issue(fields=issue_dict)
    print(str.format('New issue created: {}', ConstructJiraLink(new_issue.key)))

    try:
        if link != '':
            jira_client.create_issue_link('Relates', new_issue.key, link)
    except Exception as e:
        print(str.format('Failed to link issue {} because:\n{}', link, e))

    webbrowser.open_new_tab(ConstructJiraLink(new_issue.key))

    return new_issue


def construct_cron_table(component, version, wiki_link, schedule, server, additional_configuration):
    table = '{panel:title=Automated Process (cron) Deployment|borderStyle=dashed|borderColor=#ccc|titleBGColor=#F7D6C1|bgColor=#FFFFCE}'
    table += construct_wikitable_head('', '')
    table += construct_wikitable_row('Wiki Link', str.format('[{}]', wiki_link))
    table += construct_wikitable_row('Version #', version)
    table += construct_wikitable_row('Deployment Artifacts', construct_deploy_folder(component, version,
                                                                                     environments[args.server[0]][
                                                                                         'static_dir']))
    table += construct_wikitable_row('Schedule', schedule)
    table += construct_wikitable_row('Server', server)
    table += construct_wikitable_row('Additional Configuration', additional_configuration)
    table += construct_wikitable_row('Source Control Revision', str.format('[{}]', extract_hg_link()))
    table += '{panel}\n'
    table += 'FYI [~rfisher] [~mmckane] [~justinmoore]'

    return table


def construct_war_table(component, version, wiki_link, additional_configuration):
    table = '{panel:title=Web Application Deployment|borderStyle=dashed|borderColor=#ccc|titleBGColor=#F7D6C1|bgColor=#FFFFCE}'
    table += construct_wikitable_head('', '')
    table += construct_wikitable_row('Wiki Link', str.format('[{}]', wiki_link))
    table += construct_wikitable_row('WAR', construct_deploy_folder(component, version,
                                                                    environments[args.server[0]]['static_dir']))
    table += construct_wikitable_row('Version #', version)
    table += construct_wikitable_row('Additional Configuration', additional_configuration)
    table += construct_wikitable_row('Source Control Revision', str.format('[{}]', extract_hg_link()))
    table += '{panel}\n'
    table += 'FYI [~rfisher] [~mmckane] [~justinmoore]'

    return table


def construct_static_content_table(component, environment, additional_configuration):
    table = '{panel:title=Static Content Deployment|borderStyle=dashed|borderColor=#ccc|titleBGColor=#F7D6C1|bgColor=#FFFFCE}'
    table += construct_wikitable_head('', '')
    table += construct_wikitable_row('Zip File', construct_static_deploy_folder(component, environment))
    table += construct_wikitable_row('Additional Configuration', additional_configuration)
    table += construct_wikitable_row('Source Control Revision', str.format('[{}]', extract_hg_link()))
    table += '{panel}\n'
    table += 'FYI [~rfisher] [~mmckane] [~justinmoore]'

    return table


def copy_artifact(artifact_filename, component, version, environment):
    target_folder = construct_deploy_folder(component, version, environment)
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
    print(str.format('Copying {} to {}', artifact_filename, target_folder))
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


major_version, minor_version, patch_version, snapshot, full_version = extract_artifact_version(pom, nsmap)
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

if args.wiki_link == '':
    wiki_link = extract_url(pom, nsmap)
    if wiki_link == '':
        print(str.format('You must include <url> tag in pom or specify -w wiki link in command'))
        exit(1)
else:
    # Wiki link specified on command line - add wiki base
    wiki_link = str.format('{}/{}', wiki_base, args.wiki_link)

if str.lower(packaging) == 'war':
    table = construct_war_table(component, full_version, wiki_link, args.additional_instructions)
elif str.lower(packaging) == 'jar':
    table = construct_cron_table(component, full_version, wiki_link, '(unchanged)', server,
                                 args.additional_instructions)
elif str.lower(packaging) == 'pom':
    static_content = True
    table = construct_static_content_table(component, environments[args.server[0]]['static_dir'],
                                           args.additional_instructions)

# Start JIRA
jira_client = JIRA(server=jira_server, basic_auth=('eau', 'b423u8b*'))

commands = ['create', 'skip-copy', 'exit']
CommandCompleter = WordCompleter(commands, ignore_case=True)

print('\n')
print(table)
print('\n')

while 1:
    print(str.format('Commands: {}', commands))
    user_input = prompt('>', completer=CommandCompleter).lower()

    if user_input == '' or user_input == 'exit':
        exit()

    if user_input == 'create':
        copy_artifact(args.artifact, component, full_version, environments[args.server[0]]['static_dir'])

    # Create Deployment Ticket
    if user_input == 'create' or user_input == 'skip-copy':
        for server_arg in args.server[:]:
            summary = str.format('Please deploy {} to {}', component, environments[server_arg]['admin_name']);
            description = table

            print(summary)
            print(description)

            deploy_issue = CreateIssue(summary, description, branchname, environments[server_arg]['server_environment'],
                                       due_date)

        exit()
