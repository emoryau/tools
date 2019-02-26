from artifactory import ArtifactoryPath

artifactoryUrl="http://repository.localedge.com/artifactory/wdp-releases"
artifactoryLogin="emory.au"
artifactoryPassword="b423u8b*"

path = ArtifactoryPath(artifactoryUrl, auth=(artifactoryLogin, artifactoryPassword))

print ([x for x in path.iterdir() if x.is_dir()])

for p in path:
    print (p)

def traversePath(path):
    for p in path.iterdir():
        if p.is_dir():
            traversePath(p)
        else:
            print (p)

traversePath(path)