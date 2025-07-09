from mcp_foundry.mcp_server import mcp
 
@mcp.resource("finetuning://format/supervised",
              description="Format specification for supervised fine-tuning files",
              mime_type="application/json")
async def supervised_format_resource() -> str:
    return """
    {
        "format_name": "supervised",
        "description": "Supervised fine-tuning format for conversational AI training",
        "structure": {
            "type": "JSONL (JSON Lines)",
            "required_fields": ["messages"],
            "schema": {
                "messages": [
                    {
                        "role": "system|user|assistant",
                        "content": "string"
                    }
                ]
            }
        },
        "example": {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is the capital of France?"},
                {"role": "assistant", "content": "The capital of France is Paris."}
            ]
        },
        "validation_rules": [
            "Each line must be a valid JSON object",
            "Must contain 'messages' field as an array",
            "Each message must have 'role' and 'content' fields",
            "Role must be one of: system, user, or assistant"
        ]
    }
    """
 
@mcp.resource("finetuning://format/dpo",
              description="Format specification for DPO (Direct Preference Optimization) fine-tuning files",
              mime_type="application/json")
async def dpo_format_resource() -> str:
    return """
    {
        "format_name": "dpo",
        "description": "DPO fine-tuning format for preference learning",
        "structure": {
            "type": "JSONL (JSON Lines)",
            "required_fields": ["input", "preferred_output", "non_preferred_output"],
            "schema": {
                "input": "object",
                "preferred_output": "array",
                "non_preferred_output": "array"
            }
        },
        "example": {
            "input": {"query": "Explain quantum computing"},
            "preferred_output": ["Quantum computing leverages quantum mechanics principles like superposition and entanglement to process information in fundamentally different ways than classical computers."],
            "non_preferred_output": ["Quantum computers are just fast computers."]
        },
        "validation_rules": [
            "Each line must be a valid JSON object",
            "Must contain 'input', 'preferred_output', and 'non_preferred_output' fields",
            "'input' must be an object (can contain any fields like query, context, etc.)",
            "'preferred_output' must be a non-empty array",
            "'non_preferred_output' must be a non-empty array"
        ]
    }
    """