#     SmartXMLAnalyser


<p align="center">
   <img src="https://github.com/Biline-dev/SmartXMLAnalyser/raw/main/logo.png" alt="Logo" />
   
</p>The goal of the hackathon is to push the boundaries of GenAI solutions by tackling challenging use cases and complex problems.


## Table of Contents 📚
- [Project Scope](#project-scope)
- [Architecture](#architecture)
- [Experiment](#experiment)
- [User Interface](#user-interface)
- [How to Run](#how-to-run)
- [Challenges Encountered](#challenges-encountered)
- [Next Steps](#next-steps)

## **Project Scope**
Imagine having to manually update and validate an XML document with hundreds of pages, it’s time-consuming and error-prone.

We chose to work on the Accenture project because we recognized the strong potential for real-world implementation of intelligent systems like the XML Analyser across a wide range of industries.

**So, what was the scope of the project?**

The goal is to develop a multi-agent application capable of automating the modification of complex XML documents. Each agent is responsible for a specific task, a validation taks, correction tasks, modification and orchestration task.



## Piepline and Architecture ️

### Global Pipeline 
This is the pipeline we plan to implement for the MVP. More details on the multi-agent architecture will be presented in the next steps.

<p align="center">
   <img src="https://www.pixenli.com/image/XGOD398p" alt="Global pipeline">
</p>

### Multi Agent Architecture

We chose a supervisor architecture to implement our system. The idea is to design and implement a pipeline that efficiently manages and coordinates the different tasks within the system.


<p align="center">
   <img src="https://www.pixenli.com/image/65hNX6OP" alt="Architecture Diagram">
</p>



The orchestration flow is synchronous and task-driven:

* The orchestrator receives an insruction/an xml file.

* It decides which agent should process the input first (e.g., Validator).

* Based on the agent’s response, the orchestrator dynamically decides the next step:

    * If errors are found, it forwards the report to the Corrector.

    * After correction, it re-validates via the Validator again.

    * For modification tasks, it triggers the Modifier.
    
    

Each agent can internally use a language model (LLM) to complete its task. These LLM calls are handled within the agent and return structured outputs back to the orchestrator.

Each agent is structured as a functional module rather than a standalone service. Agents can:

   * Call internal LLMs (via Snowflake Cortex in our case).

   * Parse and modify specific XML fragments.

   * Return actionable instructions.


## Experimentation with Scenarios

If a user sends a corrupted file (e.g., a missing closing tag, a malformed tag, or incorrect format), such issues can be handled at the orchestrator level before the file is even sent to the agents.

A user can also send an instruction that will be processed by the orchestrator.

The orchestrator checks the reliability of the input using guardrails. If the instruction aligns with the system's supported tasks namely correction, deletion, or addition of elements in XML then it will be forwarded to the appropriate agent. Any other instructions will not be sent to the modifier or corrector agents.

### Scenario 1: With Validator Agent

If the XML file is syntactically correct, it goes through the validator agent, which checks if it conforms to the s1000d XML standards.The validation agent searches for the XSD schema that corresponds to the XML file sent by the user.
If the file is valid, it is sent directly to the orchestrator.
Otherwise, the validator returns a list of errors to the LLM, which generates a report with instructions to correct the document and sends it to the orchestrator.

Example Avec `mistra-large`: 

```python

prompt = f"XML validation error: {cleaned_error}"

    sql = """
    SELECT SNOWFLAKE.cortex.COMPLETE(
        'mistral-large',
        CONCAT('You are an expert in XML schema validation. Give instruction to correct each error in the xml code: ', 
               '{}', 
               '\\n\\nPlease explain: 1) What is causing this error,  2) How to fix it, 3) Example of correct XML structure')
    )
    """.format(prompt)
               
```

Output : 
```
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
        it
```

We also return a list of error paths.

**Why adding a corrector is important?**

Keeping validation role and corrector role separate help:

* Makes the system easier to debug, test, and maintain.

* Keeps each agent focused and specialized.

### Scenario 2: With Corrector Agent

The orchestrator decides to send the report coming from the validator to the corrector The orchestrator sends the report from the validator to the corrector agent, which applies the necessary corrections based on the provided instructions and returns the corrected file to the orchestrator (a prompt chaining process) . The orchestrator then sends the file back to the validator. This cycle continues until the file is clean, a human intervenes, or a predefined threshold is reached.

The corrector receives a report with a clear **error paths**, allowing it to focus only on the necessary XML fragment without parsing the entire file. 

Example of the fragment:
```
<identAndStatusSection>
      <dmAddress>
         <dmIdent>
            <dmCode modelIdentCode="BRAKE" systemDiffCode="AAA" systemCode="DA1" subSystemCode="0" subSubSystemCode="AA" assyCode="ABC" disassyCode="DEF" disassyCodeVariant="GHI" infoCode="341" infoCodeVariant="A" itemLocationCode="A"/><language countryIsoCode="US" languageIsoCode="en"/>
```

### Scenario 3: With Modifier Agent

#### Modification Workflow
When a user submits a modification instruction (add, delete, update), the LLM analyzes this request and decides to call the modifier agent. Once the modifications are completed, the result is returned to the orchestrator, which then proceeds with validation.
#### Optimization of XML Element Targeting
To optimize the identification of elements to modify, we drew inspiration from the method used by the validator agent that provides XPath locations of errors. This approach helps the agent precisely target the relevant fragments.
We implemented a technique using cosine similarity between:

* Keywords (elements <keyword>) extracted from XML files
* Key terms identified in the instructions sent by the user

The system only selects an XPath when the cosine similarity is greater than 0.5. Once an XML element is identified, the system traverses up the structure to determine the appropriate context.
This approach, however, requires validation through additional testing across different use cases to confirm its effectiveness.


## 🚀 How to Run the Project  



