from validator import run_validation_workflow

def handle_message(message: dict) -> dict:
    xml_path = message.get("xml_path")
    if not xml_path:
        return {"status": "error", "message": "Missing 'xml_path' in message"}
    
    return run_validation_workflow(xml_path)
