from utils.xml_utils import extract_instructions_from_file
from connectors.snowflake_conn import get_snowflake_connection
from agent_corrector import corrector_agent
from agent_validator import agent_validator
from agent_modifier import agent_modifier


def call_corrector_agent(xml_file_path, suggestion, xpath):
    print("🛠️ Appel à l'agent correcteur")
    xml_file_correct_path = corrector_agent(xml_file_path, suggestion, xpath)
    return xml_file_correct_path


def call_modifier_agent(xml_file_path, instructions):
    print("📝 Appel à l'agent modificateur")
    agent_modifier(xml_file_path, instructions)
    return xml_file_path


def orchestrator_llm(status, suggestions, instructions, xml_file_path, xpath, has_been_modified):
    # Nettoyage des entrées
    status_clean = status.replace("'", "''").replace("\n", " ").replace("\r", " ") if status else ""
    suggestions_clean = suggestions.replace("'", "''").replace("\n", " ").replace("\r", " ") if suggestions else ""
    instructions_clean = instructions.replace("'", "''").replace("\n", " ").replace("\r", " ") if instructions else ""

    # Prompt amélioré
    prompt = f"""
    Vous êtes un agent orchestrateur responsable de vérifier, corriger et modifier un fichier XML.

    Statut actuel du fichier XML : {status_clean}
    Le fichier a-t-il déjà été modifié ? : {"oui" if has_been_modified else "non"}

    Voici les suggestions de correction (si nécessaire) : {suggestions_clean}
    Voici les instructions pour la modification : {instructions_clean}

    Règles :
    - Si le fichier nest pas valide, répondez "correction".
    - Si le fichier est valide mais na pas encore été modifié, répondez "modification".
    - Si le fichier est modifié mais na pas encore été validé, répondez "correction".
    - Si le fichier est valide et a déjà été modifié, répondez "stop".
    - La validation doit se faire après chaque modification et correction.

    Répondez uniquement par : "correction", "modification" ou "stop".
    """

    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()

        sql = """
        SELECT SNOWFLAKE.cortex.COMPLETE(
            'claude-3-5-sonnet',
            '{}'
        )
        """.format(prompt)

        cursor.execute(sql)
        result = cursor.fetchone()

        if result and result[0]:
            response = result[0]
            decision = response.strip().lower().split()[0]
            print(f"🧠 Décision extraite de l'agent orchestrateur : {decision}")

            if decision == "correction":
                print("❌ Correction requise.")
                xml_file_path = call_corrector_agent(xml_file_path, suggestions, xpath)
            elif decision == "modification":
                print("✅ Modification requise.")
                xml_file_path = call_modifier_agent(xml_file_path, instructions)
            elif decision == "stop":
                print("🛑 Le fichier est valide et a été modifié. Arrêt du pipeline.")
            else:
                raise ValueError(f"Décision inattendue de Mistral : {decision}")

            return xml_file_path, decision
        else:
            raise ValueError("Aucune réponse obtenue de Mistral")

    except Exception as e:
        print(f"Erreur lors de l'appel à Mistral : {e}")
        import traceback
        print(traceback.format_exc())
        raise RuntimeError(f"Échec de l'agent orchestrateur : {str(e)}")

    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()


if __name__ == "__main__":
    xml_file_path = "data/TC1_additions_1/base_documents/DMC-BRAKE-AAA-DA1-00-00-00AA-341A-A_002-00_en-US.XML"
    instructions = "data/TC1_additions_1/instructions/"

    should_continue = True
    has_been_modified = False

    while should_continue:
        print(f"🔍 Validation du fichier : {xml_file_path}")
        status, suggestions, xpath = agent_validator(xml_file_path)

        xml_file_path, decision = orchestrator_llm(
            status, suggestions, instructions, xml_file_path, xpath, has_been_modified
        )
        if decision == "modification":
            has_been_modified = True
        elif decision == "stop":
            should_continue = False

    print(f"\n✅ Le fichier XML final est valide et prêt : {xml_file_path}")
