import xml.etree.ElementTree as xml
import re


def namespace(element):
	m = re.match(r'\{(.*)\}', element.tag)
	return m.group(1) if m else ''


def get_version_from_pom(pom_file_name):
	pom_file = xml.parse(pom_file_name)
	root = pom_file.getroot()
	namespace_map = {'ns': namespace(root)}
	return root.find('./ns:version', namespace_map).text

print(get_version_from_pom('pom.xml'))
