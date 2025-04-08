from agent_corrector import handle_xml_correction

if __name__ == "__main__":
    xml_file = "data/TC1_additions_1/base_documents/DMC-BRAKE-AAA-DA1-00-00-00AA-341A-A_002-00_en-US.XML"
    instruction = """

    🔧 LLM Suggestion:

            1) The error is caused by missing required attributes in the XML instance and an incorrect attribute name. The XML schema defines a complex type "dmCodeElemType" with several required attributes such as 'subSubSystemCode', 'assyCode', 'disassyCode', 'disassyCodeVariant', but these attributes are missing in the XML instance. Additionally, there is an incorrect attribute 'subSubSriant' in the XML instance, but the schema defines 'subSubSystemCode'.

            2) To fix the error, you need to add the missing required attributes to the XML instance and correct the incorrect attribute name. Make sure that the attribute names in the XML instance match the attribute names defined in the XML schema.

            3) Here is an example of the correct XML structure:

            ```xml
            <dmCode modelIdentCode="BRAKE"
                    systemDiffCode="AAA"
                    systemCode="DA1"
                    subSystemCode="0"
                    subSubSystemCode="AA"
                    assyCode="ABC"
                    disassyCode="DEF"
                    disassyCodeVariant="GHI"
                    infoCode="341"
                    infoCodeVariant="A"
                    itemLocationCode="A" />
            ```"""
    xpath = ["/dmodule/identAndStatusSection/dmAddress/dmIdent/dmCode"]
    result = handle_xml_correction(xml_file=xml_file, instruction=instruction, xpath=xpath)
    if result["status"] == "success":
        print(result["message"])
    else:
        print(f"Échec: {result['message']}")