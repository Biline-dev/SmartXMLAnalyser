from validator import run_validator_agent

def handle_message(message: dict) -> dict:
    xml_path = message.get("xml_path")
    if not xml_path:
        return {"status": "error", "message": "Missing 'xml_path' in message"}
    
    status, suggestions = run_validator_agent(xml_path)
    return status, suggestions
