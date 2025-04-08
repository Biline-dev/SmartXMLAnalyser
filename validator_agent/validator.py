from utils.xml_utils import validate_xml_and_extract_paths
from connectors.snowflake_conn import insert_error_to_snowflake
from connectors.cortex_llm import explain_error_with_llm
import os

from lxml import etree

def run_validator_agent(xml_path: str):
    filename = os.path.basename(xml_path)  # Assuming the filename is the last part of the path
    parser = etree.XMLParser(recover=True)
    
    try:
        tree = etree.parse(xml_path, parser)
        tree.write(xml_path, pretty_print=True, encoding="utf-8", xml_declaration=True)
        print(f"Fichier XML {filename} analysé et reformaté.")
    except etree.XMLSyntaxError as syntax_err:
        error_msg = str(syntax_err)
        print(f"Erreur de syntaxe XML: {error_msg}")
        insert_error_to_snowflake(filename, "invalid", error_msg, "/", "/", "Erreur de syntaxe critique")
        return
    except Exception as e:
        print(f"Erreur lors de l'analyse du fichier: {str(e)}")
        return
    
    try:
        error_msg, error_paths = validate_xml_and_extract_paths(xml_path, tree)
        if not error_msg:
            insert_error_to_snowflake(filename, "valid", "/", "/", "/", "/")
            print("✅ XML is valid according to the schema.")
        else:
            print("❌ XML is invalid. Analyzing...\n")
            explanation = explain_error_with_llm(error_msg)
            print("🔧 LLM Suggestion:\n")
            print(explanation)
            llm_suggestion = explanation  # The suggestion provided by LLM
            # Insert the error details into Snowflake
            insert_error_to_snowflake(filename, "invalid", "error_msg", "/", " ".join(error_paths), llm_suggestion)
    except Exception as e:
        print(f"Error: {e}")
    
