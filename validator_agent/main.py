from agent_validator import handle_message


def agent_validator(xml_file):
    validity, suggestions = handle_message({"xml_path": xml_file})
    if validity == "valid":
        return validity
    elif validity == "invalid":
        return validity, suggestions
    else:
        raise ValueError("Error validor !")
    
if __name__ == "__main__":
    xml_file = "data/TC1_additions_1/base_documents/DMC-BRAKE-AAA-DA1-00-00-00AA-341A-A_002-00_en-US.XML"
    agent_validator(xml_file)