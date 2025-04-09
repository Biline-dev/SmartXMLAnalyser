from validator import run_validator_agent

def handle_message(message: dict) -> dict:
    xml_path = message.get("xml_path")
    if not xml_path:
        return {"status": "error", "message": "Missing 'xml_path' in message"}
    
    status, suggestions = run_validator_agent(xml_path)
    return status, suggestions


def agent_validator(xml_file):
    validity, suggestions = handle_message({"xml_path": xml_file})
    print(validity)
    if validity == "valid":
        return validity
    elif validity == "invalid":
        return validity, suggestions
    else:
        raise ValueError("Error validor !")