from agent_validator import handle_message

if __name__ == "__main__":
    xml_file = "data/TC1_additions_1/base_documents/DMC-BRAKE-AAA-DA1-00-00-00AA-341A-A_002-00_en-US.XML"
    result = handle_message({"xml_path": xml_file})
    print(result)
