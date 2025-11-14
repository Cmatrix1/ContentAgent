"""
AI client for generating copywriting using Google Generative AI.
"""
import json
import logging
from typing import Dict, Optional

from django.conf import settings
from google import genai
from google.genai import types

from apps.copywriting.services.prompts import (
    build_generate_copywriting_prompt,
    build_regenerate_section_prompt,
)


logger = logging.getLogger(__name__)


def get_client():
    """
    Get configured GenAI client instance.
    This can be easily swapped with other LLM providers.
    """
    api_key = settings.GEMINI_API_KEY

    if not api_key:
        logger.warning("GEMINI_API_KEY not configured. Using mock responses.")
        return None
    
    return genai.Client(api_key=api_key)


def get_generation_config(response_format: str = "text") -> types.GenerateContentConfig:
    """
    Get generation configuration from Django settings.
    
    Args:
        response_format: Either "json" for JSON responses or "text" for plain text
    
    Returns:
        GenerateContentConfig instance with settings from environment
    """
    config_params = {
        "temperature": settings.GEMINI_TEMPERATURE,
        "top_p": settings.GEMINI_TOP_P,
        "top_k": settings.GEMINI_TOP_K,
        "max_output_tokens": settings.GEMINI_MAX_OUTPUT_TOKENS,
    }
    
    if response_format == "json":
        config_params["response_mime_type"] = "application/json"
    
    return types.GenerateContentConfig(**config_params)


def call_llm(prompt: str, response_format: str = "text") -> str:
    """
    Make a call to the LLM with the given prompt.
    
    Args:
        prompt: The prompt to send to the LLM
        response_format: Either "json" or "text"
    
    Returns:
        The LLM response text
    
    Raises:
        Exception: If the LLM call fails
    """
    client = get_client()
    
    if not client:
        raise Exception("AI client not configured. Please set GEMINI_API_KEY.")
    
    generation_config = get_generation_config(response_format)
    
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL_NAME,
        contents=prompt,
        config=generation_config,
    )
    
    return response.text


def generate_copywriting(inputs: dict, search_results: Optional[list] = None) -> dict:
    """
    Send structured prompt to LLM and return JSON output.
    
    Args:
        inputs: Dictionary containing:
            - title: Project title
            - description: Project description
            - platform: Target platform
            - user_description: Optional user note
            - subtitle: Optional subtitle transcript
            - subtitle_language: Language of the subtitle transcript
        search_results: Optional list of selected search results with title and snippet
    
    Returns:
        Dictionary with generated copywriting sections
    """
    prompt = build_generate_copywriting_prompt(inputs, search_results)
    result = call_llm(prompt, response_format="json").strip()
    
    # Clean up markdown code blocks if present
    if result.startswith('```'):
        result = result.split('```')[1]
        if result.startswith('json'):
            result = result[4:]
    
    outputs = json.loads(result)
    
    if isinstance(outputs, list):
        logger.error(f"LLM returned a list instead of dict. Converting to dict format.")
        if outputs and isinstance(outputs[0], dict):
            outputs = outputs[0]
        else:
            raise ValueError("LLM returned a list but expected a dictionary with copywriting sections")
    
    if not isinstance(outputs, dict):
        raise ValueError(f"LLM returned invalid type: {type(outputs)}. Expected dictionary.")
    
    logger.info(f"Successfully generated copywriting for {inputs.get('title')}")
    return outputs


def regenerate_section(context: dict, section: str, instruction: str) -> str:
    """
    Send partial prompt for regeneration and return single string.
    
    Args:
        context: Dictionary containing project context:
            - title: Project title
            - description: Project description
            - subtitle: Optional subtitle transcript
            - subtitle_language: Language of the subtitle transcript
            - old_value: Current value of the section
        section: Section name to regenerate
        instruction: User instruction for regeneration
    
    Returns:
        New text for the section
    """
    prompt = build_regenerate_section_prompt(context, section, instruction)
    
    try:
        result = call_llm(prompt, response_format="text")
        logger.info(f"Successfully regenerated section: {section}")
        return result.strip()
        
    except Exception as e:
        logger.error(f"Error regenerating section: {e}")
        return f"[Error regenerating {section}]: {str(e)}"

