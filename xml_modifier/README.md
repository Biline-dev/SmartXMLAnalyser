# XML Modifier Tool for S1000D Documentation

## Overview

This tool provides automated modification of S1000D-compliant XML documents using AI models. It processes XML files according to natural language instructions while ensuring compliance with S1000D standards.

## Key Features

- **S1000D Compliance**: Built-in knowledge of S1000D Issue 4.1+ standards
- **AI-Powered Modifications**: Uses various AI models to interpret and apply changes
- **Multiple Operation Types**: Supports add, modify, and delete operations
- **Focused Processing**: Targets specific XML sections while maintaining document integrity
- **Validation**: Includes XML validation and comparison tools

## Requirements

- Python 3.8+
- Required packages (install via `pip install -r requirements.txt`):
  - `snowflake-connector-python`
  - `python-dotenv`
  - `lxml`

## Configuration

1. Create a `.env` file with your Snowflake credentials:
   ```
   SNOWFLAKE_ACCOUNT=your_account
   SNOWFLAKE_USERNAME=your_username
   SNOWFLAKE_PASSWORD=your_password
   SNOWFLAKE_DATABASE=your_database
   SNOWFLAKE_SCHEMA=your_schema
   SNOWFLAKE_WAREHOUSE=your_warehouse
   SNOWFLAKE_ROLE=your_role
   ```

## Available Models

The tool supports multiple AI models including:
- Claude 3 Sonnet
- Gemma 7B
- Various LLaMA models (3.1-405b, 3.3-70b, etc.)
- Mistral models
- Snowflake Arctic

## Usage

### Command Line Interface

```bash
python xml_modifier.py \
    --xml "path/to/input.xml" \
    --instructions "path/to/instructions_directory/" \
    --output "path/to/output_directory/" \
    --expected "path/to/expected_result.xml" \
    --model "model_name"
```

### Parameters

| Parameter       | Description                                                                 |
|-----------------|-----------------------------------------------------------------------------|
| `--xml`         | Path to the base XML file to modify                                         |
| `--instructions`| Directory containing instruction files (`.txt`)                             |
| `--output`      | Directory where results will be saved                                       |
| `--expected`    | Path to the expected result XML file for comparison                         |
| `--model`       | Name of the AI model to use (default: "sonnet")                             |

### Instruction Files

- Create one or more `.txt` files in the instructions directory
- Each file should contain a single modification instruction in natural language
- Files are processed in alphabetical order

## Output

The tool generates:
1. Intermediate XML files after each instruction
2. A final result XML file
3. A comparison with the expected result (if provided)

## S1000D Compliance

The tool enforces S1000D standards including:
- Proper XML structure and naming conventions
- Data module code (DMC) format requirements
- Content section requirements
- Table and illustration standards

## Troubleshooting

- **XML Validation Errors**: Ensure input XML is well-formed
- **Instruction Clarity**: Provide clear, specific instructions
- **Model Selection**: Try different models if results are unsatisfactory

## License

[Note defined]

## Support

For issues or questions, please contact [your support contact].