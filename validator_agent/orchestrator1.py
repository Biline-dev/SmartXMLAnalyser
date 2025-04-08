from main import agent_validator
from connectors.cortex_llm import prompt_correction_with_llm, prompt_modifier_with_llm
from utils.xml_utils import extract_instructions_from_file
from connectors.snowflake_conn import get_snowflake_connection
import os
import sys
from dotenv import load_dotenv

def call_corrector_agent(suggestion, xml_file_path):
    print("🛠️ Appel à l'agent correcteur")
    #prompt = prompt_correction_with_llm(suggestion)
    # Corrector_Agent(prompt, xml_file_path)  # Remplacer par l'appel à l'agent correcteur
    return xml_file_path

def call_modifier_agent(instructions, xml_file_path):
    print("📝 Appel à l'agent modificateur")
    #prompt = prompt_modifier_with_llm(instructions)
    # Modifier_Agent(prompt, xml_file_path)  # Remplacer par l'appel à l'agent modificateur
    return xml_file_path

import os

def orchestrator_llm(status, suggestions, instructions, xml_file_path):
    
    # Nettoyage des entrées
    status_clean = status.replace("'", "''").replace("\n", " ").replace("\r", " ") if status else ""
    suggestions_clean = suggestions.replace("'", "''").replace("\n", " ").replace("\r", " ") if suggestions else ""
    instructions_clean = instructions.replace("'", "''").replace("\n", " ").replace("\r", " ") if instructions else ""
    
    # Création du prompt
    prompt = f"""
    Vous êtes un agent orchestrateur qui décide quelle action entreprendre sur un fichier XML.
    
    Voici le statut du fichier XML : {status_clean}
    Voici les suggestions fournies pour la correction : {suggestions_clean}
    Voici les instructions pour la modification : {instructions_clean}
    
    Décidez si nous devons procéder à une correction ou une modification du fichier XML.
    Retournez uniquement "correction" ou "modification" comme réponse.
    """
    
    try:
        # Obtenir une connexion à Snowflake
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        
        sql = """
        SELECT SNOWFLAKE.cortex.COMPLETE(
            'mistral-large',
            '{}'
        )
        """.format(prompt)
        
        # Exécution de la requête
        cursor.execute(sql)
        result = cursor.fetchone()
        
        # Récupération et nettoyage de la réponse
        if result and result[0]:
            response = result[0]
            print(f"Réponse brute de Mistral: {response}")
            
            # Nettoyer et extraire la décision
            decision = response.strip().lower()
            print(f"Décision extraite: {decision}")
            
            # Prise de décision en fonction de la réponse
            if "modification" in decision:
                print("✅ L'agent orchestrateur décide de passer à la modification.")
                return call_modifier_agent(instructions, xml_file_path)
            elif "correction" in decision:
                print("❌ L'agent orchestrateur décide d'appeler l'agent correcteur.")
                return call_corrector_agent(suggestions, xml_file_path)
            else:
                raise ValueError(f"Décision inattendue de Mistral : {decision}")
        else:
            raise ValueError("Aucune réponse obtenue de Mistral")
        
    except Exception as e:
        print(f"Erreur lors de l'appel à Mistral : {e}")
        import traceback
        print(traceback.format_exc())
        raise RuntimeError(f"Échec de la décision de l'agent orchestrateur: {str(e)}")
    finally:
        # Fermeture des ressources Snowflake
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    xml_file_path = "data/TC1_additions_1/base_documents/DMC-BRAKE-AAA-DA1-00-00-00AA-341A-A_002-00_en-US.XML"
    instructions_file_path = "data/TC1_additions_1/instructions/instruction_all.txt"

    instructions = extract_instructions_from_file(instructions_file_path)

    is_valid = False

    while not is_valid:
        print(f"🔍 Validation du fichier : {xml_file_path}")
        status, suggestions = agent_validator(xml_file_path)

        # L'agent orchestrateur prend la décision d'appeler l'agent correcteur ou modificateur via Mistral
        xml_file_path = orchestrator_llm(status, suggestions, instructions, xml_file_path)

        # Re-validation après correction ou modification
        status, suggestions = agent_validator(xml_file_path)
        if status == 'valid':
            print("✅ Fichier XML final est valide !")
            is_valid = True
        else:
            print("🔁 Le fichier est toujours invalide, nouvelle itération...")

    print(f"✅ Fichier XML final est valide : {xml_file_path}")
