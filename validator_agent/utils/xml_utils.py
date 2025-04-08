from lxml import etree
import xmlschema
from config import SCHEMA_URL_MAP

def extract_schema_location(xml_path: str) -> str:
    tree = etree.parse(xml_path)
    root = tree.getroot()
    xsi_ns = "http://www.w3.org/2001/XMLSchema-instance"
    schema_location = root.attrib.get(f"{{{xsi_ns}}}noNamespaceSchemaLocation") \
                      or root.attrib.get(f"{{{xsi_ns}}}schemaLocation")
    if not schema_location:
        raise ValueError("No schema location found in XML.")
    if " " in schema_location:
        schema_location = schema_location.split()[-1]
    if schema_location in SCHEMA_URL_MAP:
        return SCHEMA_URL_MAP[schema_location]
    else:
        raise ValueError(f"Unknown schema location: {schema_location}")

def validate_xml(xml_path: str, schema_path: str) -> str | None:
    schema = xmlschema.XMLSchema(schema_path)
    if schema.is_valid(xml_path):
        return None
    try:
        schema.validate(xml_path)
    except xmlschema.XMLSchemaValidationError as e:
        return str(e)

def extract_instance_and_path(error_msg: str) -> (str, str):
    import re
    path_pattern = r"Path:\s+([^\n]+)"
    instance_pattern = r"Instance:\s+(<[^>]+>)"

    path_match = re.search(path_pattern, error_msg)
    instance_match = re.search(instance_pattern, error_msg)

    path = path_match.group(1) if path_match else "N/A"
    instance = instance_match.group(1) if instance_match else "N/A"

    return instance, path
