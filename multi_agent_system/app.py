import streamlit as st
import time
from connectors.snowflake_conn import get_snowflake_connection
from utils.xml_utils import extract_instructions_from_file
from agent_corrector import corrector_agent
from agent_validator import agent_validator
from agent_modifier import agent_modifier


def log_and_display(log_placeholder, full_log, message):
    full_log.append(message)
    log_placeholder.code("\n".join(full_log))
    time.sleep(0.3)


def call_corrector_agent(xml_file_path, suggestion, xpath, log_placeholder, full_log):
    log_and_display(log_placeholder, full_log, "🛠️ Appel à l'agent correcteur")
    xml_file_correct_path = corrector_agent(xml_file_path, suggestion, xpath)
    return xml_file_correct_path


def call_modifier_agent(xml_file_path, instructions, log_placeholder, full_log):
    log_and_display(log_placeholder, full_log, "📝 Appel à l'agent modificateur")
    agent_modifier(xml_file_path, instructions)
    return xml_file_path


def orchestrator_llm(status, suggestions, instructions, xml_file_path, xpath, has_been_modified, log_placeholder, full_log):
    status_clean = status.replace("'", "''").replace("\n", " ").replace("\r", " ") if status else ""
    suggestions_clean = suggestions.replace("'", "''").replace("\n", " ").replace("\r", " ") if suggestions else ""
    instructions_clean = instructions.replace("'", "''").replace("\n", " ").replace("\r", " ") if instructions else ""

    prompt = f"""
    Vous êtes un agent orchestrateur responsable de vérifier, corriger et modifier un fichier XML.

    Statut actuel du fichier XML : {status_clean}
    Le fichier a-t-il déjà été modifié ? : {"oui" if has_been_modified else "non"}

    Voici les suggestions de correction (si nécessaire) : {suggestions_clean}
    Voici les instructions pour la modification : {instructions_clean}

    Règles :
    - Si le fichier n'est pas valide, répondez "correction".
    - Si le fichier est valide mais n'a pas encore été modifié, répondez "modification".
    - Si le fichier est modifié mais n'a pas encore été validé, répondez "correction".
    - Si le fichier est valide et a déjà été modifié, répondez "stop".
    - La validation doit se faire après chaque modification et correction.

    Répondez uniquement par : "correction", "modification" ou "stop".
    """

    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()

        sql = f"""
        SELECT SNOWFLAKE.cortex.COMPLETE(
            'claude-3-5-sonnet',
            $$ {prompt} $$
        )
        """

        cursor.execute(sql)
        result = cursor.fetchone()

        if result and result[0]:
            response = result[0]
            decision = response.strip().lower().split()[0]
            log_and_display(log_placeholder, full_log, f"🧠 Décision extraite de l'agent orchestrateur : {decision}")

            if decision == "correction":
                log_and_display(log_placeholder, full_log, "❌ Correction requise.")
                xml_file_path = call_corrector_agent(xml_file_path, suggestions, xpath, log_placeholder, full_log)
            elif decision == "modification":
                log_and_display(log_placeholder, full_log, "✅ Modification requise.")
                log_and_display(log_placeholder, full_log, f"📜 Instructions : {instructions_clean}")
                xml_file_path = call_modifier_agent(xml_file_path, instructions, log_placeholder, full_log)
            elif decision == "stop":
                log_and_display(log_placeholder, full_log, "🛑 Le fichier est valide et a été modifié. Arrêt du pipeline.")
            else:
                raise ValueError(f"Décision inattendue : {decision}")

            return xml_file_path, decision
        else:
            raise ValueError("Aucune réponse obtenue de Mistral")

    except Exception as e:
        import traceback
        log_and_display(log_placeholder, full_log, f"🚨 Erreur lors de l'appel à Mistral : {e}")
        log_and_display(log_placeholder, full_log, traceback.format_exc())
        raise RuntimeError(f"Échec de l'agent orchestrateur : {str(e)}")

    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()


def main():
    st.set_page_config(page_title="Orchestrateur XML Multi-Test", layout="wide")
    st.title("Orchestrateur XML - Multi-tests")

    test_cases = {
        "Test 1": {
            "xml_file_path": "data/TC1_additions_1/base_documents/DMC-BRAKE-AAA-DA1-00-00-00AA-341A-A_002-00_en-US.XML",
            "instructions": "data/TC1_additions_1/instructions",
        },
        "Test 2": {
            "xml_file_path": "data/TC2_additions_2/base_documents/DMC-S1000DBIKE-AAA-D00-00-00-00AA-121A-A_009-00_en-US.XML",
            "instructions": "data/TC2_additions_2/instructions",
        },
        "Test 3": {
            "xml_file_path": "data/TC3_modify_n_delete/base_documents/DMC-S1000DBIKE-AAA-D00-00-00-00AA-258B-A_002-00_en-US.XML",
            "instructions": "data/TC3_modify_n_delete/instructions",
        },
        "Test 4": {
            "xml_file_path": "data/TC4_all_modifications/base_documents/DMC-S1000DBIKE-AAA-D00-00-01-00AA-720A-A_002-00_en-US.XML",
            "instructions": "data/TC4_all_modifications/instructions",
        },

        # Tu peux ajouter d'autres tests ici facilement
    }

    selected_test = st.selectbox(" Choisir un test à exécuter", list(test_cases.keys()))
    st.markdown(f"**Test sélectionné** : `{selected_test}`")

    log_placeholder = st.empty()
    full_log = []

    if st.button("🚀 Lancer ce test"):
        test = test_cases[selected_test]
        xml_file_path = test["xml_file_path"]
        instructions = test["instructions"]

        should_continue = True
        has_been_modified = False

        while should_continue:
            log_and_display(log_placeholder, full_log, f"🔍 Validation du fichier : {xml_file_path}")
            status, suggestions, xpath = agent_validator(xml_file_path)

            xml_file_path, decision = orchestrator_llm(
                status, suggestions, instructions, xml_file_path, xpath, has_been_modified,
                log_placeholder, full_log
            )

            if decision == "modification":
                has_been_modified = True
            elif decision == "stop":
                should_continue = False

        log_and_display(log_placeholder, full_log, f"\n✅ Le fichier XML final est valide et prêt : {xml_file_path}")


if __name__ == "__main__":
    main()
