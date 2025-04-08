
from main import agent_validator
from connectors.cortex_llm import prompt_correction_with_llm, prompt_modifier_with_llm
from utils.xml_utils import extract_instructions_from_file


def call_corrector_agent(suggestion, xml_file_path):
    print("corrector agent")
    prompt = prompt_correction_with_llm(suggestion)
    #Corrector_Agent(prompt, xml_file_path)

def call_modifier_agent(instructions, xml_file_path):
    print("modifier agent")
    prompt = prompt_modifier_with_llm(instructions)
    #Modifier_Agent(prompt, xml_file_path)

if __name__ == "__main__":
    xml_file_path = "data/TC1_additions_1/base_documents/DMC-BRAKE-AAA-DA1-00-00-00AA-341A-A_002-00_en-US.XML"
    instructions_file_path = "data/TC1_additions_1/instructions/instruction_all.txt"

    instructions = extract_instructions_from_file(instructions_file_path)

    is_valid = False

    while not is_valid:
        print(f"🔍 Validation du fichier : {xml_file_path}")
        status, suggestions = agent_validator(xml_file_path)

        if status == 'valid':
            print("✅ Fichier valide. Passage à la modification...")
            xml_file_path = call_modifier_agent(instructions, xml_file_path)
        else:
            print("❌ Fichier invalide. Appel de l'agent correcteur...")
            xml_file_path = call_corrector_agent(suggestions, xml_file_path)

        # Re-validation après correction ou modification
        status, suggestions = agent_validator(xml_file_path)
        if status == 'valid':
            print("✅ Fichier XML final est valide !")
            is_valid = True
        else:
            print("🔁 Le fichier est toujours invalide, nouvelle itération...")

    print(f"✅ Final XML is valid: {xml_file_path}")

