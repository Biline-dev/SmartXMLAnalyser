from agent import handle_message

def agent_validator(path):
    result = handle_message({"xml_path": path})
    print("result ------------->", result)
    validity = result["validity"]
    llm_explanation = result["llm_explanation"]

    if validity == "valid":
        return validity, llm_explanation
    elif validity == "invalid":
        return validity, llm_explanation
    else:
        raise ValueError("Error validor !")


if __name__ == "__main__":
    agent_validator()