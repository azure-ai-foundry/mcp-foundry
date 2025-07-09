import os
import json
import logging
import sys
import requests
from mcp_foundry.mcp_server import mcp
from mcp.server.fastmcp import Context
from dotenv import load_dotenv
 
# Configure logging (following the pattern from other tools)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp_foundry_finetuning")
 
load_dotenv()
 
# Use consistent environment variable names following the codebase pattern
azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
api_version = os.environ.get("AZURE_OPENAI_API_VERSION")
api_key = os.environ.get("AZURE_OPENAI_API_KEY")
 
@mcp.tool()
def list_finetuning_jobs(ctx: Context):
    """
    MCP-compatible function to list all finetuning jobs using Azure OpenAI API.
   
    Returns:
        List of dictionaries containing job ID and status.
    """
 
    if not azure_endpoint or not api_key:
        return json.dumps({
            "error": "Missing required environment variables: 'AZURE_OPENAI_ENDPOINT' or 'AZURE_OPENAI_API_KEY'."
        })
 
    url = f"{azure_endpoint}/openai/fine_tuning/jobs?api-version={api_version}"
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }
 
    response = requests.get(url, headers=headers)
 
    if response.status_code == 200:
        jobs_data = response.json()
        return [{"job_id": job["id"], "status": job["status"]} for job in jobs_data.get("data", [])]
    else:
        print(f"Failed to retrieve jobs. Status code: {response.status_code}")
        return []
   
@mcp.tool()
def get_finetuning_job_events(ctx: Context, job_id: str):
    """
    MCP-compatible function to retrieve all events for a specific finetuning job.
    It also returns the billing details.
 
    Returns:
        List of event details including timestamp and message.
    """
 
    if not azure_endpoint or not api_key:
        return json.dumps({
            "error": "Missing required environment variables: 'AZURE_OPENAI_ENDPOINT' or 'AZURE_OPENAI_API_KEY'."
        })
   
    url = f"{azure_endpoint}/openai/fine_tuning/jobs/{job_id}/events?api-version={api_version}"
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
 
    response = requests.get(url, headers=headers)
 
    if response.status_code == 200:
        events_data = response.json()
        return [
            {
                "timestamp": event.get("created_at"),
                "message": event.get("message")
            }
            for event in events_data.get("data", [])
        ]
    else:
        print(f"Failed to retrieve events. Status code: {response.status_code}")
        return []
 
 
@mcp.tool()
def fetch_finetuning_status(ctx: Context, job_id: str) -> str:
    """
    Fetches the status of a fine-tuning job using Azure OpenAI API.
 
    Parameters:
    - job_id: The ID of the fine-tuning job.
 
    Returns:
    - Job status information as a JSON string.
    """
 
    if not azure_endpoint or not api_key:
        return json.dumps({
            "error": "Missing required environment variables: 'AZURE_OPENAI_ENDPOINT' or 'AZURE_OPENAI_API_KEY'."
        })
 
    url = f"{azure_endpoint}/openai/fine_tuning/jobs/{job_id}?api-version={api_version}"
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }
 
    try:
        logger.info(f"Fetching fine-tuning job status for job_id: {job_id}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        job_data = response.json()
 
        return json.dumps({
            "job_id": job_data.get("id"),
            "status": job_data.get("status"),
            "model": job_data.get("model"),
            "created_at": job_data.get("created_at"),
            "finished_at": job_data.get("finished_at"),
            "hyperparameters": job_data.get("hyperparameters"),
            "fine_tuned_model": job_data.get("fine_tuned_model"),
            "trained_tokens": job_data.get("trained_tokens"),
            "result_files": job_data.get("result_files", []),
            "training_files": job_data.get("training_files", []),
            "validation_files": job_data.get("validation_files", []),
            "estimated_finish": job_data.get("estimated_finish"),
            "error": job_data.get("error", {})
        })
 
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching fine-tuning job status: {str(e)}")
        return json.dumps({"error": f"Request error: {str(e)}"})
    except Exception as e:
        logger.error(f"Unexpected error fetching fine-tuning job status: {str(e)}")
        return json.dumps({"error": f"Unexpected error: {str(e)}"})
 
@mcp.tool()    
def get_finetuning_metrics(ctx, job_id: str) -> str:
    """
    Retrieves fine-tuning metrics if the job has succeeded.
    Calls fetch_finetuning_status to confirm job completion.
    Then fetches the result.csv content using the result_file_id.
    """
    job_data = fetch_finetuning_status(ctx, job_id)
    # Parse the JSON string to a dictionary
    job_data = json.loads(job_data)
    status = job_data.get("status")
    if status == "succeeded":
        result_files = job_data.get("result_files", [])
        file_id = result_files[0] if result_files else None
 
        file_url = f"{azure_endpoint}/openai/files/{file_id}/content?api-version={api_version}"
        headers = {
            "api-key": api_key,
            "Content-Type": "application/json"
        }
 
        try:
            logger.info(f"Fetching result file content for file_id: {file_id}")
            file_response = requests.get(file_url, headers=headers, timeout=10)
            file_response.raise_for_status()
            result_csv_content = file_response.content.decode('utf-8')
 
            return json.dumps({
                "job_id": job_data.get("id"),
                "status": status,
                "result_file_id": file_id,
                "result_file_url": file_url,
                "result_csv_content": result_csv_content
            })
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching result file: {str(e)}")
            return json.dumps({"error": f"Request error fetching result file: {str(e)}"})
        except Exception as e:
            logger.error(f"Unexpected error fetching result file: {str(e)}")
            return json.dumps({"error": f"Unexpected error fetching result file: {str(e)}"})
    else:
        return json.dumps({
            "job_id": job_data.get("id"),
            "status": status,
            "message": "Job has not succeeded yet."
        })
 
@mcp.tool()
def validate_file_sample(ctx: Context, file_id: str, sample_size: int = 10) -> str:
    """
    Fetches a sample of lines from a file for inspection.
    
    Parameters:
    - file_id: ID of the file to sample
    - sample_size: Number of lines to sample (default: 10)
    
    Returns:
    - JSON string with file sample
    """
    if not azure_endpoint or not api_key:
        return json.dumps({
            "error": "Missing required environment variables: 'AZURE_OPENAI_ENDPOINT' or 'AZURE_OPENAI_API_KEY'."
        })
    
    file_url = f"{azure_endpoint}/openai/files/{file_id}/content?api-version={api_version}"
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(file_url, headers=headers, timeout=10)
        response.raise_for_status()
        lines = response.text.strip().split('\n')
        
        if not lines or all(not line.strip() for line in lines):
            return json.dumps({
                "file_id": file_id,
                "error": "File is empty or contains only whitespace."
            })
        
        sample = []
        invalid_json_lines = []
        
        for i, line in enumerate(lines[:sample_size]):
            if line.strip():
                try:
                    parsed = json.loads(line)
                    sample.append(parsed)
                except json.JSONDecodeError:
                    invalid_json_lines.append(i + 1)
        
        return json.dumps({
            "file_id": file_id,
            "sample": sample,
            "total_lines": len(lines),
            "sample_size": len(sample),
            "invalid_json_lines": invalid_json_lines
        })
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching file: {str(e)}")
        return json.dumps({
            "file_id": file_id,
            "error": f"Request error: {str(e)}"
        })
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return json.dumps({
            "file_id": file_id,
            "error": f"Unexpected error: {str(e)}"
        })

@mcp.tool()
def create_finetuning_job(
    ctx: Context,
    job_type: str,
    training_file_id: str,
    validation_file_id: str = None,
    model: str = "gpt-4o-mini-2024-07-18",
    hyperparameters: dict = None
) -> str:
    """
    Creates a fine-tuning job. Azure OpenAI will validate the file format.
    
    Parameters:
    - job_type: Type of finetuning job ('supervised' or 'dpo')
    - training_file_id: ID of the training file
    - validation_file_id: Optional ID of the validation file
    - model: Base model to fine-tune (default: gpt-4o-mini-2024-07-18)
    - hyperparameters: Optional hyperparameters
    
    Returns:
    - JSON string with job result or Azure API error
    """

    if not azure_endpoint or not api_key:
        return json.dumps({
            "error": "Missing required environment variables: 'AZURE_OPENAI_ENDPOINT' or 'AZURE_OPENAI_API_KEY'."
        })
    
    if job_type not in ['supervised', 'dpo']:
        return json.dumps({
            "error": "Invalid job_type. Must be 'supervised' or 'dpo'."
        })
    
    logger.info(f"Creating {job_type} finetuning job with file: {training_file_id}")
    
    url = f"{azure_endpoint}/openai/fine_tuning/jobs?api-version={api_version}"
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }
    
    body = {
        "model": model,
        "training_file": training_file_id,
    }
    
    if validation_file_id:
        body["validation_file"] = validation_file_id
    
    if hyperparameters:
        body["hyperparameters"] = hyperparameters
    else:
        if job_type == 'dpo':
            body["hyperparameters"] = {
                "n_epochs": 3,
                "batch_size": 1,
                "learning_rate_multiplier": 1.8
            }
        else:
            body["hyperparameters"] = {
                "n_epochs": 3,
                "batch_size": 1,
                "learning_rate_multiplier": 2
            }
    
    if job_type == 'dpo':
        method = {"type": "dpo"}
        if hyperparameters and "dpo" in hyperparameters:
            method.update(hyperparameters["dpo"])
        body["method"] = method
    
    try:
        response = requests.post(url, headers=headers, json=body, timeout=30)
        
        if response.status_code >= 400:
            error_data = response.json()
            error_message = error_data.get('error', {}).get('message', 'Unknown error')
            logger.error(f"API error creating finetuning job: {error_message}")
            
            # Azure API will return specific format errors
            return json.dumps({
                "success": False,
                "error": error_message,
                "status_code": response.status_code,
                "error_details": error_data,
                "hint": f"See resource finetuning://format/{job_type} for expected format"
            })
        
        job_data = response.json()
        return json.dumps({
            "success": True,
            "job_id": job_data.get("id"),
            "status": job_data.get("status"),
            "job_type": job_type,
            "model": job_data.get("model"),
            "training_file": job_data.get("training_file"),
            "created_at": job_data.get("created_at")
        })
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error creating finetuning job: {str(e)}")
        return json.dumps({
            "success": False,
            "error": f"Request error: {str(e)}"
        })
    except Exception as e:
        logger.error(f"Unexpected error creating finetuning job: {str(e)}")
        return json.dumps({
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        })