from utils.xml_utils import (
    extract_schema_location,
    validate_xml,
    extract_instance_and_path
)
from connectors.snowflake_conn import insert_error_to_snowflake
from connectors.cortex_llm import explain_error_with_llm
import os

def run_validation_workflow(xml_path: str) -> dict:
   
    schema_path = extract_schema_location(xml_path)
    error_msg = validate_xml(xml_path, schema_path)
    filename = os.path.basename(xml_path)

    if not error_msg:
        insert_error_to_snowflake(filename, "valid", "/", "/", "/", "/")
        return {
            "status": "success",
            "validity": "valid",
            "filename": filename
        }

    explanation = explain_error_with_llm(error_msg)
    instance, path = extract_instance_and_path(error_msg)

    insert_error_to_snowflake(filename, "invalid", error_msg, instance, path, explanation)

    return {
        "status": "success",
        "validity": "invalid",
        "filename": filename,
        "error_message": error_msg,
        "llm_explanation": explanation,
        "instance": instance,
        "path": path
    }

    
