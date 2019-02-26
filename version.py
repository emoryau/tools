import xml.etree.ElementTree as xml

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

pom = xml.parse('pom.xml')
nsmap = {'m': 'http://maven.apache.org/POM/4.0.0'}
major_version, minor_version, patch_version, snapshot, full_version = extract_artifact_version(pom, nsmap)

print(full_version)