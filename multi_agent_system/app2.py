import streamlit as st
import os
import tempfile
import shutil
from utils.xml_utils import extract_instructions_from_file
from connectors.snowflake_conn import get_snowflake_connection
from agent_corrector import corrector_agent
from agent_validator import agent_validator
from agent_modifier import agent_modifier
import time

def log_and_display(log_placeholder, full_log, message):
    full_log.append(message)
    log_placeholder.code("\n".join(full_log))
    time.sleep(0.3)


def call_corrector_agent(xml_file_path, suggestion, xpath, log_placeholder, full_log):
    log_and_display(log_placeholder, full_log, " Appel à l'agent correcteur")
    xml_file_correct_path = corrector_agent(xml_file_path, suggestion, xpath)
    return xml_file_correct_path


def call_modifier_agent(xml_file_path, instructions, log_placeholder, full_log):
    log_and_display(log_placeholder, full_log, " Appel à l'agent modificateur")
    agent_modifier(xml_file_path, instructions)
    return xml_file_path

def process_file(file_path, instructions, log_placeholder):
    """Process the uploaded file with the given instructions"""
    should_continue = True
    has_been_modified = False
    
    # Create a progress tracker
    progress_bar = st.progress(0)
    status_message = st.empty()
    
    # Placeholder for real-time preview
    preview_container = st.container()
    preview_placeholder = preview_container.empty()
    
    # Store original content for comparison
    with open(file_path, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    # Capture original file name for later reference
    original_file_name = os.path.basename(file_path)
    
    # Show initial file content
    preview_placeholder.markdown("### Version originale du fichier")
    preview_placeholder.code(original_content, language="xml")
    
    iteration = 0
    max_iterations = 10  # Safety limit
    
    full_log = []  # Initialize the log
    
    # Keep track of the current file path as it may change during iterations
    current_file_path = file_path

    while should_continue and iteration < max_iterations:
        iteration += 1
        progress = min(0.1 * iteration, 0.9)  # Cap at 90% until complete
        progress_bar.progress(progress)
        
        status_message.text(f"Iteration {iteration}: Validating file...")
        status, suggestions, xpath = agent_validator(current_file_path)
        log_and_display(log_placeholder, full_log, f"Iteration {iteration}: Validation done.")
        
        status_message.text(f"Iteration {iteration}: Orchestrating next action...")
        new_file_path, decision = orchestrator_llm(
            status, suggestions, instructions, current_file_path, xpath, has_been_modified, log_placeholder, full_log
        )
        
        # Update the current file path
        current_file_path = new_file_path
        
        if decision == "modification" or decision == "correction":
            has_been_modified = True
            status_message.text(f"Iteration {iteration}: File modified")
            
            # Update real-time preview after modification
            with open(current_file_path, 'r', encoding='utf-8') as f:
                modified_content = f.read()
            
            # Check if the file is in the corrected_files directory
            dir_name = os.path.dirname(current_file_path)
            if "corrected_files" in dir_name:
                log_and_display(log_placeholder, full_log, f"Fichier modifié détecté dans le dossier corrected_files")
            
            # Show modified content with comparison
            preview_placeholder.empty()  # Clear previous content
            preview_placeholder.markdown("### Aperçu des modifications en temps réel")
            
            # Create tabs for original and modified
            orig_tab, mod_tab, diff_tab = preview_placeholder.tabs(["Original", "Modifié", "Différences"])
            
            with orig_tab:
                st.code(original_content, language="xml")
            
            with mod_tab:
                st.code(modified_content, language="xml")
                
            with diff_tab:
                try:
                    import difflib
                    diff = difflib.unified_diff(
                        original_content.splitlines(),
                        modified_content.splitlines(),
                        lineterm='',
                        fromfile=original_file_name,
                        tofile=os.path.basename(current_file_path),
                        n=3  # context lines
                    )
                    
                    diff_text = '\n'.join(diff)
                    st.code(diff_text, language="diff")
                except Exception as e:
                    st.error(f"Impossible d'afficher les différences: {str(e)}")
                    
        elif decision == "stop":
            should_continue = False
            status_message.text("Processing complete!")
    
    # Complete the progress bar
    progress_bar.progress(1.0)
    
    if iteration >= max_iterations and should_continue:
        st.warning("Reached maximum iterations. Process may not be complete.")
    
    # Ensure we're showing the final comparison between original and final modified file
    # This is especially important if the file is in the corrected_files directory
    try:
        # First check if there's a corrected files directory with our file
        original_basename = os.path.basename(file_path)
        possible_corrected_path = os.path.join(os.path.dirname(os.path.dirname(current_file_path)), 
                                            "corrected_files", original_basename)
        print("possible_corrected_path------->",possible_corrected_path)
        if os.path.exists(possible_corrected_path):
            log_and_display(log_placeholder, full_log, f"Fichier corrigé trouvé: {possible_corrected_path}")
            with open(possible_corrected_path, 'r', encoding='utf-8') as f:
                final_modified_content = f.read()
        else:
            # If not found, use the current file path
            with open(current_file_path, 'r', encoding='utf-8') as f:
                final_modified_content = f.read()
        
        # Show final comparison
        preview_placeholder.empty()
        preview_placeholder.markdown("### Comparaison finale")
        
        final_orig_tab, final_mod_tab, final_diff_tab = preview_placeholder.tabs(["Original", "Modifié", "Différences"])
        
        with final_orig_tab:
            st.code(original_content, language="xml")
        
        with final_mod_tab:
            st.code(final_modified_content, language="xml")
            
        with final_diff_tab:
            import difflib
            final_diff = difflib.unified_diff(
                original_content.splitlines(),
                final_modified_content.splitlines(),
                lineterm='',
                fromfile=original_file_name,
                tofile="Fichier modifié final",
                n=3  # context lines
            )
            
            final_diff_text = '\n'.join(final_diff)
            st.code(final_diff_text, language="diff")
    
    except Exception as e:
        log_and_display(log_placeholder, full_log, f"Erreur lors de la comparaison finale: {str(e)}")
    
    return current_file_path



def orchestrator_llm(status, suggestions, instructions, xml_file_path, xpath, has_been_modified, log_placeholder, full_log):
    # Nettoyage des entrées
    status_clean = status.replace("'", "''").replace("\n", " ").replace("\r", " ") if status else ""
    suggestions_clean = suggestions.replace("'", "''").replace("\n", " ").replace("\r", " ") if suggestions else ""

    prompt = f"""
    Vous êtes un agent orchestrateur responsable de vérifier, corriger et modifier un fichier XML.

    Statut actuel du fichier XML : {status_clean}
    Le fichier a-t-il déjà été modifié ? : {"oui" if has_been_modified else "non"}

    Voici les suggestions de correction (si nécessaire) : {suggestions_clean}

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
            log_and_display(log_placeholder, full_log, f"🧠 Décision extraite de l'agent orchestrateur : {decision}")

            if decision == "correction":
                log_and_display(log_placeholder, full_log, "❌ Correction requise.")
                xml_file_path = call_corrector_agent(xml_file_path, suggestions, xpath, log_placeholder, full_log)
            elif decision == "modification":
                log_and_display(log_placeholder, full_log, "✅ Modification requise.")
                xml_file_path = call_modifier_agent(xml_file_path, instructions, log_placeholder, full_log)
            elif decision == "stop":
                log_and_display(log_placeholder, full_log, "🛑 Le fichier est valide et a été modifié. Arrêt du pipeline.")
            else:
                raise ValueError(f"Décision inattendue de Mistral : {decision}")

            return xml_file_path, decision
        else:
            raise ValueError("Aucune réponse obtenue de Mistral")

    except Exception as e:
        log_and_display(log_placeholder, full_log, f"Erreur lors de l'appel à Mistral : {str(e)}")
        import traceback
        log_and_display(log_placeholder, full_log, traceback.format_exc())
        raise RuntimeError(f"Échec de l'agent orchestrateur : {str(e)}")

    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

st.markdown("""
    <style>
    .title-style {
        font-size: 4em;
        font-weight: bold;
        color: white;
        text-shadow: 1px 1px 4px rgba(0,0,0,0.15);
        text-align: center;
    }

    .subtitle-style {
        font-size: 1.3em;
        color: white;
        text-align: center;
        margin-bottom: 30px;
    }
    .collaptitle{
        border:1px solid red        
    }
    .collapsible {
        padding: 5px;
        border-radius: 8px;
        margin-top: 5px;
    }
    
    /* Styles pour les onglets et boutons */
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 10px;
        padding: 10px 24px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #45a049;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Style pour les zones de texte */
    .stTextArea textarea {
        border-radius: 8px;
        border: 1px solid #ddd;
    }
    
    /* Style pour les expanders */
    .streamlit-expanderHeader {
        font-weight: bold;
        color: #2c3e50;
    }
    </style>
""", unsafe_allow_html=True)


def main():
    st.markdown('<div class="title-style">Smart - XML</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle-style">Assistant intelligent de modification de documentation</div>', unsafe_allow_html=True)

    example_prompt = """
    ✨ Exemples d'instructions pour modifier le document XML :

     ➕  Ajout : Add a step titled 'Final Safety Check' with: 'Ensure area is clean'.

     🔄  Modication : Replace 'Initial Setup' with 'System Initialization Procedure.'

     🗑️  Suppression : Remove the step titled 'Pressure Sensor Calibration.'

    """.strip()

    with st.container():
        st.markdown("#### 📝 Instructions")
        tab1, tab2 = st.tabs(["✍️  Prompt   ", "   📁  Fichier d'instructions"])

        log_placeholder = st.empty()
        instructions_text = ""
        instruction_file = None

        with tab1:
            st.info("Rédigez vos instructions pour modifier le document XML.")
            instructions_text = st.text_area(
                "Instructions",
                height=180,
                placeholder=example_prompt,
                key="text_instructions_area"
            )

        with tab2:
            st.info("Téléchargez un fichier texte contenant vos instructions.")
            instruction_file = st.file_uploader(
                "Uploader un fichier .txt",
                type=["txt"],
                key="instruction_file_uploader"
            )

    st.markdown("---")
    st.markdown("#### 📄 Fichier XML")
    xml_file = st.file_uploader(
        "Uploader un fichier XML",
        type=["xml", "XML"],
        key="xml_file_uploader"
    )

    xml_content = ""
    if xml_file:
        st.success(f"Fichier chargé : {xml_file.name}")
        xml_content = xml_file.getvalue().decode("utf-8")
        with st.expander("Aperçu du contenu XML"):
            st.code(xml_content, language="xml")

    instructions = ""
    if instructions_text.strip():
        instructions = instructions_text.strip()
    elif instruction_file:
        instructions = instruction_file.getvalue().decode("utf-8").strip()

    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        process_clicked = st.button("🚀  Lancer le traitement", key="process_button", use_container_width=True)

    with st.expander("ℹ️ Comment ça marche ?"):
        st.markdown("""
        <div class="collapsible">
        <ol>
            <li><strong>Upload</strong> votre fichier XML</li>
            <li><strong>Rédigez</strong> vos instructions de modification ou uploadez un fichier .txt</li>
            <li><strong>Cliquez sur "Lancer le traitement"</strong> pour lancer la transformation</li>
            <li><strong>Téléchargez</strong> votre fichier modifié !</li>
        </ol>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("#### 📊 Logs d'exécution")
    log_container = st.container()
    log_placeholder = log_container.empty()

    status_container = st.empty()

    st.markdown("#### 👁️ Aperçu des modifications")
    st.info("Les modifications du fichier s'afficheront ici en temps réel pendant le traitement.")
    preview_expander = st.expander("Visualiser les changements", expanded=True)

    if process_clicked:
        if not xml_file:
            st.warning("⚠️ Merci d'uploader un fichier XML")
        elif not instructions:
            st.error("❌ Veuillez fournir des instructions valides")
        else:
            with st.spinner("🔧 Traitement en cours..."):
                try:
                    # Sauvegarde du fichier original pour traitement
                    temp_file_path = f"./uploaded_{xml_file.name}"
                    with open(temp_file_path, "wb") as f:
                        f.write(xml_file.getvalue())

                    # Appel du traitement
                    processed_file_path = process_file(temp_file_path, instructions, log_placeholder)

                    # Vérifie si une version modifiée est dans corrected_files/
                    original_filename = os.path.basename(temp_file_path)
                    possible_corrected_path = os.path.join("corrected_files", original_filename)

                    corrected_file_path = possible_corrected_path if os.path.exists(possible_corrected_path) else processed_file_path

                    if os.path.exists(corrected_file_path):
                        with open(corrected_file_path, "rb") as f:
                            file_content = f.read()

                        success_message = st.success("✅ Fichier traité avec succès !")

                        col1, col2, col3 = st.columns([1, 2, 1])
                        with col2:
                            st.download_button(
                                label="⬇️ Télécharger le fichier modifié",
                                data=file_content,
                                file_name="processed_" + os.path.basename(corrected_file_path),
                                mime="application/xml",
                                key="download_button",
                                use_container_width=True
                            )

                        # Affichage fichiers + diff
                        with open(temp_file_path, 'r', encoding='utf-8') as f:
                            original_text = f.readlines()
                        with open(corrected_file_path, 'r', encoding='utf-8') as f:
                            modified_text = f.readlines()

                        with preview_expander:
                            col1, col2 = st.columns(2)

                            with col1:
                                st.markdown("##### 🧾 Fichier original")
                                st.code("".join(original_text), language="xml")

                            with col2:
                                st.markdown("##### 🛠️ Fichier modifié")
                                st.code("".join(modified_text), language="xml")

                            st.markdown("##### 🔍 Différences entre original et modifié")
                            diff = difflib.HtmlDiff(wrapcolumn=80).make_table(
                                original_text,
                                modified_text,
                                "Original",
                                "Modifié",
                                context=True,
                                numlines=2
                            )
                            st.components.v1.html(diff, scrolling=True, height=400)

                    else:
                        st.error("❌ Fichier modifié introuvable.")

                except Exception as e:
                    st.error(f"❌ Erreur lors du traitement : {str(e)}")


if __name__ == "__main__":
    main()
