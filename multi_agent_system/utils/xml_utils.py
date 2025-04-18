import os
import xmlschema
from lxml.etree import _ElementTree
import re
def extract_schema_locations(tree: _ElementTree) -> list:
    """Extract all schema locations from the XML file."""
   
    root = tree.getroot()
    xsi_ns = "http://www.w3.org/2001/XMLSchema-instance"
    
    # Look for schemaLocation or noNamespaceSchemaLocation attributes
    schema_locations = root.attrib.get(f"{{{xsi_ns}}}noNamespaceSchemaLocation") \
                        or root.attrib.get(f"{{{xsi_ns}}}schemaLocation")
    if not schema_locations:
        raise ValueError(f"No schema location found in.")
    
    # If there are multiple schema locations, split them
    return schema_locations.split()  # Return as a list of schema URIs

def get_schema_path(schema_location: str, base_path: str) -> str:
    """Resolve the schema location to a file path or URL."""
    # If schema_location is an absolute URL, return it
  
    if schema_location.startswith("http://") or schema_location.startswith("https://"):
        return schema_location
    
    print(f"Schema location: {schema_location}")
    # If it's a relative file path, resolve it based on the base path of the XML file
    schema_file_path = os.path.join(os.path.dirname(base_path), schema_location)
    
    # Check if the file exists locally
    if os.path.isfile(schema_file_path):
        return schema_file_path
    
    # If it's not found, you can raise an error or search in predefined directories
    # For example, search in a folder of known schemas
    known_schemas_dir = "data/xml_schema_flat"  # Define the base directory for schemas
    potential_schema_path = os.path.join(known_schemas_dir, schema_location)
    if os.path.isfile(potential_schema_path):
        return potential_schema_path
    
    raise ValueError(f"Schema not found: {schema_location} (searched in {known_schemas_dir})")

def validate_xml_and_extract_paths(xml_path: str, tree: _ElementTree) -> (str, list):
    """Validate the XML file using its corresponding schema and extract paths."""
    # Extract the schema location from the XML
    schema_locations = extract_schema_locations(tree)
    all_errors = []  # To store all error messages
    error_paths = set()  # Use a set to store unique paths
    for schema_location in schema_locations:
        # Resolve the schema path (either a URL or a local file path)
        schema_path = get_schema_path(schema_location, xml_path)
        
        # Load the XML schema
        schema = xmlschema.XMLSchema(schema_path)
        
        namespaces = {k: v for k, v in tree.getroot().nsmap.items() if k is not None}
        
        # Validate the XML against the schema
        if not schema.is_valid(xml_path, namespaces=namespaces):
            # Collect validation errors for this schema
            errors = schema.iter_errors(xml_path, namespaces=namespaces)
            for error in errors:
                # Extract the error message
                error_msg = str(error)
                
                # Append the error message to the list of all errors
                all_errors.append(error_msg)
                
                # Extract path and instance using regular expressions
                instance, path = extract_instance_and_path(error_msg)
                
                # Append the path to the list (you can append instance as well if needed)
                error_paths.add(path)
    
    # Return both concatenated error messages and the list of error paths
    return "\n".join(all_errors) if all_errors else None, list(error_paths)

def extract_instance_and_path(error_msg: str) -> (str, str):
    """Extract the path and instance from the error message using regex."""
    path_pattern = r"Path:\s+([^\n]+)"
    instance_pattern = r"Instance:\s+(<[^>]+>)"

    path_match = re.search(path_pattern, error_msg)
    instance_match = re.search(instance_pattern, error_msg)

    path = path_match.group(1) if path_match else "N/A"
    instance = instance_match.group(1) if instance_match else "N/A"

    return instance, path


def extract_instructions_from_file(file_path: str) -> str:
    try:
        with open(file_path, 'r') as file:
            instructions = file.readlines()
        
        instructions = [line.strip() for line in instructions if line.strip()]
        instructions_text = "\n".join(instructions)
        
        return instructions_text
    except Exception as e:
        return f"Erreur lors de la lecture du fichier : {str(e)}"
    

def extract_instructions_from_prompt(prompt: str) -> list[str]:
    # Split en fonction des sauts de ligne doubles ou simples
    raw_instructions = [line.strip() for line in prompt.split('\n') if line.strip()]
    
    # S'assurer que chaque instruction se termine par un point
    instructions = []
    for instr in raw_instructions:
        if not instr.endswith('.'):
            instr += '.'
        instructions.append(instr)
        
    return instructions