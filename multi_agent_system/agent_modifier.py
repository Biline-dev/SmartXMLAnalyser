import os
from dotenv import load_dotenv
import snowflake.connector
import re
import xml.etree.ElementTree as ET
import lxml.etree as lxmlET
from copy import deepcopy

# Load .env file
load_dotenv()

# Read variables
sf_account = os.getenv("SNOWFLAKE_ACCOUNT")
sf_user = os.getenv("SNOWFLAKE_USERNAME")
sf_password = os.getenv("SNOWFLAKE_PASSWORD")
sf_database = os.getenv("SNOWFLAKE_DATABASE")
sf_schema = os.getenv("SNOWFLAKE_SCHEMA")
sf_warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
sf_role = os.getenv("SNOWFLAKE_ROLE")

# Connect to Snowflake
conn = snowflake.connector.connect(
    user=sf_user,
    password=sf_password,
    account=sf_account,
    warehouse=sf_warehouse,
    database=sf_database,
    schema=sf_schema,
    role=sf_role
)

## S1000D norms library - organized by different aspects of the specification
S1000D_NORMS = {
    "general": [
        "All XML must comply with S1000D Issue 4.1 or higher schema definitions",
        "Element and attribute names must use camelCase notation as defined in S1000D",
        "All IDs must be globally unique within the data module",
    ],
    "data_module": [
        "Data modules must include identificNumber, dmCode, and dmTitle elements",
        "Data module code (DMC) must follow the S1000D standard format",
        "Each data module must contain both identAndStatusSection and contentSection",
    ],
    "content": [
        "Content must use the standard S1000D elements like para, warning, caution",
        "All references must use the dmRef element with proper reference attributes",
        "All procedural steps must be contained within proceduralStep elements",
    ],
    "tables": [
        "Tables must use the formal table structure with table, tgroup, thead, tbody elements",
        "Tables must have explicit column specifications using colspec elements",
        "Table cells must use entry elements with appropriate attributes",
    ],
    "illustrations": [
        "Illustrations must use the figure element with the correct attribute structure",
        "All graphics must be referenced using the graphic element with appropriate attributes",
        "Illustration control numbers (ICN) must follow the S1000D standard format",
    ]
}

## Prompt template definition
PROMPTS = {
    "delete": "Given the XML and the instruction to DELETE a component, perform the operation ensuring strict compliance with S1000D.",
    "add": "Given the XML and the instruction to ADD a component, insert it following the S1000D rules exactly.",
    "modify": "Given the XML and the instruction to MODIFY a component, apply the change according to strict S1000D compliance."
}

# Available models
AVAILABLE_MODELS = {
    # Anthropic models
    "sonnet": "claude-3-5-sonnet",
    
    # Gemma model
    "gemma-7b": "gemma-7b",
    
    # Jamba models
    "jamba-mini": "jamba-1.5-mini",
    "jamba-large": "jamba-1.5-large",
    "jamba-instruct": "jamba-instruct",
    
    # LLaMA models
    "llama2-70b": "llama2-70b-chat",
    "llama3-8b": "llama3-8b",
    "llama3-70b": "llama3-70b",
    "llama3.1-8b": "llama3.1-8b",
    "llama3.1-70b": "llama3.1-70b",
    "llama3.1-405b": "llama3.1-405b",
    "llama3.2-1b": "llama3.2-1b",
    "llama3.2-3b": "llama3.2-3b",
    "llama3.3-70b": "llama3.3-70b",
    "llama4-maverick": "llama4-maverick",
    
    # Mistral models
    "mistral-7b": "mistral-7b",
    "mistral-large": "mistral-large",
    "mistral-large2": "mistral-large2",
    "mixtral-8x7b": "mixtral-8x7b",
    
    # Reka models
    "reka-core": "reka-core",
    "reka-flash": "reka-flash",
    
    # Snowflake models
    "snowflake-arctic": "snowflake-arctic",
    "snowflake-llama3.1-405b": "snowflake-llama-3.1-405b",
    "snowflake-llama3.3-70b": "snowflake-llama-3.3-70b"
}

def get_prompt(instruction_type):
    return PROMPTS.get(instruction_type.lower(), "Unknown instruction type.")

def analyze_xml_content(xml_content):
    """Analyze XML content to determine which S1000D norms are most relevant."""
    relevant_categories = []
    
    if "<table" in xml_content or "<tgroup" in xml_content:
        relevant_categories.append("tables")
    
    if "<figure" in xml_content or "<graphic" in xml_content:
        relevant_categories.append("illustrations")
    
    if "<proceduralStep" in xml_content:
        relevant_categories.append("content")
    
    if "<dmCode" in xml_content or "<identNumber" in xml_content:
        relevant_categories.append("data_module")
    
    # Always include general norms
    if "general" not in relevant_categories:
        relevant_categories.append("general")
        
    return relevant_categories

def analyze_instruction(instruction_text):
    """Analyze instruction to determine which S1000D norms are most relevant."""
    instruction_lower = instruction_text.lower()
    relevant_categories = []
    
    if "table" in instruction_lower or "column" in instruction_lower or "row" in instruction_lower:
        relevant_categories.append("tables")
    
    if "figure" in instruction_lower or "illustration" in instruction_lower or "graphic" in instruction_lower:
        relevant_categories.append("illustrations")
    
    if "step" in instruction_lower or "procedure" in instruction_lower or "warning" in instruction_lower:
        relevant_categories.append("content")
    
    if "data module" in instruction_lower or "dmc" in instruction_lower:
        relevant_categories.append("data_module")
    
    return relevant_categories

def extract_element_path_from_instruction(instruction, xml_str):
    """Extract the target element path from the instruction."""
    instruction_lower = instruction.lower()
    
    # Look for common section names in the instruction
    target_sections = []
    if "main procedure" in instruction_lower or "mainprocedure" in instruction_lower:
        target_sections.append("mainProcedure")
    if "preliminary" in instruction_lower or "preliminaryrqmts" in instruction_lower:
        target_sections.append("preliminaryRqmts")
    if "safety" in instruction_lower:
        target_sections.append("reqSafety")
    if "content" in instruction_lower:
        target_sections.append("content")
    if "procedure" in instruction_lower:
        target_sections.append("procedure")
    
    # Try to find the specified element in the XML
    try:
        # Use lxml instead of ElementTree for getpath functionality
        root = lxmlET.fromstring(xml_str.encode('utf-8'))
        tree = lxmlET.ElementTree(root)  # Create an ElementTree object
        
        if not target_sections:
            # If no specific section mentioned, make a guess based on action
            if "step" in instruction_lower or "procedural" in instruction_lower:
                target_sections = ["mainProcedure"]
                
        # Return the path to the first found target section
        for section in target_sections:
            elements = root.xpath(f"//*[local-name()='{section}']")
            if elements:
                # Get the path to this element using the tree object
                path = tree.getpath(elements[0])
                return path
    except Exception as e:
        print(f"Error extracting path: {e}")
    
    # Default path if nothing specific found
    return "/dmodule/content/procedure/mainProcedure"

class ModifierAgent:
    def __init__(self, conn, model_name="sonnet"):
        self.conn = conn
        self.model = AVAILABLE_MODELS.get(model_name.lower(), AVAILABLE_MODELS["sonnet"])
        print(f"Using model: {self.model}")

    def get_relevant_s1000d_norms(self, xml_content, instruction):
        """Get relevant S1000D norms based on XML content and instruction."""
        xml_categories = analyze_xml_content(xml_content)
        instruction_categories = analyze_instruction(instruction)
        
        # Combine categories from both analyses
        relevant_categories = list(set(xml_categories + instruction_categories))
        
        # Compile relevant norms
        norms = []
        for category in relevant_categories:
            norms.extend(S1000D_NORMS.get(category, []))
        
        # Remove duplicates while preserving order
        unique_norms = []
        for norm in norms:
            if norm not in unique_norms:
                unique_norms.append(norm)
        
        return "\n".join(unique_norms)

    def generate_focused_prompt(self, xml_content, instruction, instruction_type, target_path):
        """Generate a prompt that focuses on a specific part of the XML."""
        base_prompt = get_prompt(instruction_type)
        relevant_norms = self.get_relevant_s1000d_norms(xml_content, instruction)
        
        # Extract the target section using lxml for better XPath support
        try:
            root = lxmlET.fromstring(xml_content.encode('utf-8'))
            target_elem = root.xpath(target_path)[0]
            target_xml = lxmlET.tostring(target_elem, encoding='unicode', pretty_print=True)
            
            # Get parent context (one level up)
            parent_path = '/'.join(target_path.split('/')[:-1])
            if parent_path:
                parent_elems = root.xpath(parent_path)
                if parent_elems:
                    parent_context = lxmlET.tostring(parent_elems[0], encoding='unicode', pretty_print=True)
                else:
                    parent_context = "Not available"
            else:
                parent_context = "Not available"
                
            return f"""{base_prompt}

---
Instruction:
{instruction}

Target XML Section Path:
{target_path}

Target XML Section:
{target_xml}

Parent Context (for reference):
{parent_context}

Full XML (for reference only - do NOT modify parts outside the target section):
{xml_content[:500]}...

Relevant S1000D Norms:
{relevant_norms}

INSTRUCTIONS:
1. Analyze the instruction carefully.
2. Modify ONLY the target XML section according to the instruction.
3. Return ONLY the modified target section with all changes implemented.
4. Maintain proper XML structure and nesting according to S1000D standards.
5. Do NOT return the full XML document - only return the exact section specified by the target path.
6. IMPORTANT: RETURN THE XML WRAPPED IN ```xml YOUR_XML_HERE ``` CODE BLOCKS.
"""
        except Exception as e:
            print(f"Error generating focused prompt: {e}")
            # Fall back to default prompt with full XML
            return self.generate_full_prompt(xml_content, instruction, instruction_type)

    def generate_full_prompt(self, xml_content, instruction, instruction_type):
        """Generate a prompt for processing the full XML document."""
        base_prompt = get_prompt(instruction_type)
        relevant_norms = self.get_relevant_s1000d_norms(xml_content, instruction)
        
        return f"""{base_prompt}

---
Instruction:
{instruction}

XML Content:
{xml_content}

Relevant S1000D Norms:
{relevant_norms}

INSTRUCTIONS:
1. You MUST return the ENTIRE XML document with ALL content preserved.
2. DO NOT use placeholders or comments like "previous content remains unchanged".
3. Include ALL original XML content in your response with the specified modifications applied.
4. Maintain all XML attributes, namespaces, and document structure.
5. Make ONLY the changes specified in the instruction.
6. IMPORTANT: RETURN THE XML WRAPPED IN ```xml YOUR_XML_HERE ``` CODE BLOCKS.
"""

    def run_model_on_prompt(self, prompt):
        # You can change this if you're using Snowflake Cortex or UDF
        
        # query = f"select SNOWFLAKE.CORTEX.COMPLETE('claude-3-5-sonnet', $$ {prompt} $$)"
        query = f"select SNOWFLAKE.CORTEX.COMPLETE('{self.model}', $$ {prompt} $$)"
        cursor = self.conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        return result[0] if result else "No result"

    def merge_xml_changes(self, original_xml, modified_section, target_path):
        """Merge the modified section back into the original XML."""
        try:
            # Extract the XML declaration and DOCTYPE if present
            xml_decl = None
            doctype = None
            
            # Check for XML declaration
            if original_xml.startswith('<?xml'):
                decl_end = original_xml.find('?>')
                if decl_end != -1:
                    xml_decl = original_xml[:decl_end+2]
            
            # Check for DOCTYPE
            doctype_start = original_xml.find('<!DOCTYPE')
            if doctype_start != -1:
                doctype_end = original_xml.find('>', doctype_start)
                if doctype_end != -1:
                    doctype = original_xml[doctype_start:doctype_end+1]

            # Parse the original XML and the modified section
            root = lxmlET.fromstring(original_xml.encode('utf-8'))
            
            # Clean up the modified section (remove leading/trailing whitespace)
            modified_section = modified_section.strip()
            
            # If the section doesn't start with '<', it might be text or invalid
            if not modified_section.startswith('<'):
                print(f"Warning: Modified section doesn't look like valid XML: '{modified_section[:30]}...'")
                return original_xml
                
            # Parse the modified section
            try:
                mod_section = lxmlET.fromstring(modified_section.encode('utf-8'))
            except Exception as e:
                print(f"Error parsing modified section: {e}")
                print(f"Modified section (first 100 chars): {modified_section[:100]}")
                return original_xml
            
            # Find the target element in the original XML
            target_elems = root.xpath(target_path)
            if not target_elems:
                print(f"Target path not found: {target_path}")
                return original_xml
                
            target_elem = target_elems[0]
            
            # Replace the target element with the modified section
            parent = target_elem.getparent()
            if parent is not None:
                index = parent.index(target_elem)
                parent.remove(target_elem)
                parent.insert(index, mod_section)
            else:
                # This would only happen if we're replacing the root element
                root = mod_section
                
            # Convert the modified XML back to a string
            result_xml = lxmlET.tostring(root, encoding='unicode', pretty_print=True)

            # Add back the XML declaration and DOCTYPE if they were present
            if xml_decl:
                result_xml = xml_decl + '\n' + result_xml
            if doctype:
                # Insert DOCTYPE after XML declaration or at the beginning
                if xml_decl:
                    result_xml = result_xml.replace(xml_decl + '\n', xml_decl + '\n' + doctype + '\n')
                else:
                    result_xml = doctype + '\n' + result_xml
                    
            return result_xml
            
        except Exception as e:
            print(f"Error merging XML changes: {e}")
            return original_xml  # Return original if merge fails

    def extract_xml_section(self, output):
        """Extract XML from the LLM output."""
        print(f"Extracting XML from output (first 100 chars): {output[:100]}...")
        
        # Check for XML code blocks
        xml_pattern = r'```xml\s*([\s\S]*?)\s*```'
        xml_match = re.search(xml_pattern, output)
        
        if xml_match:
            extracted = xml_match.group(1).strip()
            print(f"Found XML in code block (first 50 chars): {extracted[:50]}...")
            return extracted
        
        # If no XML code blocks, look for XML tags
        if output.strip().startswith('<') and '>' in output:
            # Try to find the first complete XML element
            start_idx = output.find('<')
            
            # Find the tag name
            tag_end = output.find(' ', start_idx + 1)
            if tag_end == -1:
                tag_end = output.find('>', start_idx + 1)
            
            if tag_end > start_idx:
                tag_name = output[start_idx+1:tag_end]
                
                # Find the matching closing tag
                closing_tag = f'</{tag_name}>'
                end_idx = output.find(closing_tag)
                
                if end_idx != -1:
                    end_idx += len(closing_tag)
                    extracted = output[start_idx:end_idx].strip()
                    print(f"Found XML by tags (first 50 chars): {extracted[:50]}...")
                    return extracted
            
            # If no matching closing tag, return everything from the first '<'
            print("No matching closing tag found, returning all content from first '<'")
            return output[start_idx:].strip()
        
        # If nothing looks like XML, return the original output
        print("No XML structure found in output")
        return output.strip()

    def process(self, xml_str, instruction, instruction_type):
        """Process the XML based on the instruction."""
        try:
            # Validate input XML
            try:
                ET.fromstring(xml_str)
            except ET.ParseError as pe:
                return ["Error: The input XML is not well-formed. Please fix XML syntax errors before processing."]
            
            # Try the focused approach first
            target_path = extract_element_path_from_instruction(instruction, xml_str)
            
            if target_path:
                print(f"Using focused approach on path: {target_path}")
                focused_prompt = self.generate_focused_prompt(xml_str, instruction, instruction_type, target_path)
                focused_output = self.run_model_on_prompt(focused_prompt)
                
                # Extract the XML section from the response
                modified_section = self.extract_xml_section(focused_output)
                
                # Merge the changes back into the original XML
                result_xml = self.merge_xml_changes(xml_str, modified_section, target_path)
                
                # Verify the result is valid XML
                try:
                    ET.fromstring(result_xml)
                    return [result_xml]
                except ET.ParseError as pe:
                    print(f"Error parsing merged XML: {pe}. Falling back to full document approach.")
            else:
                print("No target path identified, falling back to full document approach")
            
            # Fall back to full document approach if focused approach fails
            print("Using full document approach")
            full_prompt = self.generate_full_prompt(xml_str, instruction, instruction_type)
            full_output = self.run_model_on_prompt(full_prompt)
            
            # Extract XML from the response
            full_xml = self.extract_xml_section(full_output)
            
            # Verify the result is valid XML
            try:
                ET.fromstring(full_xml)
                return [full_xml]
            except ET.ParseError as pe:
                print(f"Error parsing full XML response: {pe}")
                # If still invalid, return with error
                return [f"Error: The LLM generated invalid XML. Original XML preserved.\n\n{xml_str}"]
                
        except Exception as e:
            print(f"Error during processing: {e}")
            return [f"Error during processing: {str(e)}. Original XML preserved.\n\n{xml_str}"]

def read_file(file_path):
    """Read a file and return its contents as a string."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def determine_instruction_type(instruction_text):
    """Determine the type of instruction based on the content."""
    instruction_lower = instruction_text.lower()
    if "delete" in instruction_lower or "remove" in instruction_lower:
        return "delete"
    elif "add" in instruction_lower or "insert" in instruction_lower:
        return "add"
    elif "modify" in instruction_lower or "change" in instruction_lower or "update" in instruction_lower:
        return "modify"
    else:
        return "modify"  # Default to modify if unclear
    
###========= FUNCTIONS FOR COMPARING THE CORRECTED RESULTS WITH THE EXPECTED FILE RESULT
import xml.etree.ElementTree as ET
from collections import defaultdict

def compare_xml_files(file1_path, file2_path, ignore_order=True):
    """
    Compare two XML files and return differences.
    
    Args:
        file1_path (str): Path to the first XML file
        file2_path (str): Path to the second XML file
        ignore_order (bool): If True, ignore order of child elements (default: True)
    
    Returns:
        dict: Dictionary containing comparison results with keys:
              - 'same_structure': True if structures match
              - 'same_values': True if all values match
              - 'differences': List of differences found
    """
    def parse_xml(file_path):
        try:
            tree = ET.parse(file_path)
            return tree.getroot()
        except ET.ParseError as e:
            raise ValueError(f"Error parsing {file_path}: {str(e)}")
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")

    def get_element_info(element):
        """Extract element information for comparison"""
        info = {
            'tag': element.tag,
            'attrib': dict(element.attrib),
            'text': element.text.strip() if element.text else None,
            'children': []
        }
        
        for child in element:
            info['children'].append(get_element_info(child))
            
        return info

    def compare_elements(elem1, elem2, path=""):
        differences = []
        current_path = f"{path}/{elem1['tag']}" if path else elem1['tag']

        # Compare tag names
        if elem1['tag'] != elem2['tag']:
            differences.append(f"Different tags at {current_path}: {elem1['tag']} vs {elem2['tag']}")

        # Compare attributes
        if elem1['attrib'] != elem2['attrib']:
            diff_attrib = set(elem1['attrib'].items()) ^ set(elem2['attrib'].items())
            differences.append(f"Different attributes at {current_path}: {diff_attrib}")

        # Compare text content
        if elem1['text'] != elem2['text']:
            differences.append(f"Different text at {current_path}: '{elem1['text']}' vs '{elem2['text']}'")

        # Compare children
        if len(elem1['children']) != len(elem2['children']):
            differences.append(f"Different number of children at {current_path}: {len(elem1['children'])} vs {len(elem2['children'])}")
        else:
            if ignore_order:
                # Group children by tag for order-independent comparison
                children1 = defaultdict(list)
                children2 = defaultdict(list)
                
                for child in elem1['children']:
                    children1[child['tag']].append(child)
                
                for child in elem2['children']:
                    children2[child['tag']].append(child)
                
                # Compare groups
                if set(children1.keys()) != set(children2.keys()):
                    differences.append(f"Different child tags at {current_path}: {set(children1.keys())} vs {set(children2.keys())}")
                else:
                    for tag in children1:
                        if len(children1[tag]) != len(children2[tag]):
                            differences.append(f"Different count of '{tag}' children at {current_path}: {len(children1[tag])} vs {len(children2[tag])}")
                        else:
                            for i, (c1, c2) in enumerate(zip(sorted(children1[tag], key=str), sorted(children2[tag], key=str))):
                                differences.extend(compare_elements(c1, c2, current_path))
            else:
                # Compare children in order
                for i, (child1, child2) in enumerate(zip(elem1['children'], elem2['children'])):
                    differences.extend(compare_elements(child1, child2, current_path))

        return differences

    # Parse both files
    root1 = parse_xml(file1_path)
    root2 = parse_xml(file2_path)
    
    # Get element information
    elem1 = get_element_info(root1)
    elem2 = get_element_info(root2)
    
    # Compare elements
    differences = compare_elements(elem1, elem2)
    
    # Prepare result
    result = {
        'same_structure': elem1['tag'] == elem2['tag'] and not differences,
        'same_values': not differences,
        'differences': differences
    }
    
    return result


###=========

def main(xml_file_path:str, instructions_directory:str, output_directory:str, expected_result:str, model_name="sonnet"):

    # Read initial XML file
    xml_content = read_file(xml_file_path)
    if not xml_content:
        print("Error: Could not read XML file.")
        return
    
    # Get all instruction files from the directory and sort them
    instruction_files = [f for f in os.listdir(instructions_directory) if f.endswith('.txt')]
    instruction_files.sort()  # Sort to ensure consistent order
    
    # Create output directory if it doesn't exist
    os.makedirs(output_directory, exist_ok=True)
    
    current_xml = xml_content
    agent = ModifierAgent(conn, model_name=model_name)
    
    print(f"Found {len(instruction_files)} instruction files to process sequentially.")
    
    # Process each instruction sequentially
    for i, instruction_file in enumerate(instruction_files):
        instruction_path = os.path.join(instructions_directory, instruction_file)
        instruction_content = read_file(instruction_path)
        
        if not instruction_content:
            print(f"Error: Could not read instruction file {instruction_file}. Skipping.")
            continue
        
        print(f"\n📝 Processing instruction {i+1}/{len(instruction_files)}: {instruction_file}")
        
        # Determine instruction type
        instruction_type = determine_instruction_type(instruction_content)
        print(f"Detected instruction type: {instruction_type}")
        
        # Process the current XML with this instruction
        results = agent.process(
            xml_str=current_xml,
            instruction=instruction_content,
            instruction_type=instruction_type
        )
        
        if results:
            # Update the current XML with the result of this instruction
            current_xml = results[0]  # Assuming process() returns a list, take the first result
            
            # Optionally save intermediate results
            intermediate_file = os.path.join(output_directory, f"intermediate_result_{i+1}.xml")
            with open(intermediate_file, 'w', encoding='utf-8') as file:
                file.write(current_xml)
            print(f"Intermediate result saved to {intermediate_file}")
        else:
            print(f"Warning: No results returned for instruction {instruction_file}")
    
    # Save the final result after all instructions have been applied
    final_output_path = os.path.join(output_directory, "DMC-BRAKE-AAA-DA1-00-00-00AA-341A-A_002-00_en-US.xml")
    with open(final_output_path, 'w', encoding='utf-8') as file:
        file.write(current_xml)
    
    print(f"\n✅ All instructions processed successfully.")
    print(f"Final result saved to {final_output_path}")

    # ======= Comparing the corrected file with the expected results
    """
    print("\n📍========[ COMPARING CORRECTED FILE WITH EXPECTED RESULT FILE ]========📍")
    result = compare_xml_files(final_output_path, expected_result)
    print("\t|- Same structure:", result['same_structure'])
    print("\t|- Same values:", result['same_values'])
    if result['differences']:
        print("Differences found:")
        for diff in result['differences']:
            print("-", diff)
    """
    # =======
    
    return current_xml

# ---- Uncomment to keep only the version of the command line you'd like to use -----

## --- Scenrio 1: All arguments are passed directly into the script---
### Command line to run with scenario 1: python3 xml_modifier.py

# File paths - replace with your actual file paths
xml_file_path = "testing_cases/TC1_additions_1/base_documents/DMC-BRAKE-AAA-DA1-00-00-00AA-341A-A_002-00_en-US.XML"
instructions_directory = "testing_cases/TC1_additions_1/instructions copy/"
output_directory = "corrected_files/"
expected_result = 'testing_cases/TC1_additions_1/expected_result/DMC-BRAKE-AAA-DA1-00-00-00AA-341A-A_002-00_en-US.XML'
model_name = 'sonnet'

if __name__ == "__main__":
    main(xml_file_path, instructions_directory, output_directory, expected_result, model_name)

def agent_modifier (xml_file_path, instructions_directory):
    output_directory = "corrected_files/"
    model_name = 'sonnet'
    expected_result = 'data/TC1_additions_1/expected_result/DMC-BRAKE-AAA-DA1-00-00-00AA-341A-A_002-00_en-US.XML'

    main(xml_file_path, instructions_directory, output_directory, expected_result, model_name)
    return expected_result


# # --- Scenrio 2: All arguments are passed using the command line interface ---
# ## example Command line to run with scenario 1: 
#     python xml_modifier.py \
#     --xml "testing_cases/TC1_additions_1/base_documents/DMC-BRAKE-AAA-DA1-00-00-00AA-341A-A_002-00_en-US.XML" \
#     --instructions "testing_cases/TC1_additions_1/instructions copy/" \
#     --output "output/" \
#     --expected "testing_cases/TC1_additions_1/expected_result/DMC-BRAKE-AAA-DA1-00-00-00AA-341A-A_002-00_en-US.XML" \
#     --model "sonnet"

# import argparse

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description='Process XML files with instructions')
#     parser.add_argument('--xml', required=True, help='Path to base XML file')
#     parser.add_argument('--instructions', required=True, help='Path to instructions directory')
#     parser.add_argument('--output', required=True, help='Path to output directory')
#     parser.add_argument('--expected', required=True, help='Path to expected result XML file')
#     parser.add_argument('--model', default='sonnet', help='Model name to use')
    
#     args = parser.parse_args()
    
#     main(
#         xml_file_path=args.xml,
#         instructions_directory=args.instructions,
#         output_directory=args.output,
#         expected_result=args.expected,
#         model_name=args.model
#     )