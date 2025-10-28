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


def generate_copywriting(inputs: dict, search_results: Optional[list] = None) -> dict:
    """
    Send structured prompt to LLM and return JSON output.
    
    Args:
        inputs: Dictionary containing:
            - title: Project title
            - description: Project description
            - platform: Target platform
            - user_description: Optional user note
        search_results: Optional list of selected search results with title and snippet
    
    Returns:
        Dictionary with generated copywriting sections
    """
    client = get_client()
    
    # Build prompt using the prompt builder
    prompt = build_generate_copywriting_prompt(inputs, search_results)
    
    # Get model configuration from settings
    model_name = settings.GEMINI_MODEL_NAME
    temperature = settings.GEMINI_TEMPERATURE
    max_tokens = settings.GEMINI_MAX_OUTPUT_TOKENS
    top_p = settings.GEMINI_TOP_P
    top_k = settings.GEMINI_TOP_K
    
    # Configure generation parameters
    generation_config = types.GenerateContentConfig(
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        max_output_tokens=max_tokens,
        response_mime_type="application/json",
    )
    
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=generation_config,
    )

    result = response.text.strip()
    if result.startswith('```'):
        result = result.split('```')[1]
        if result.startswith('json'):
            result = result[4:]
    
    outputs = json.loads(result)
    logger.info(f"Successfully generated copywriting for {inputs.get('title')}")
    return outputs


def regenerate_section(context: dict, section: str, instruction: str) -> str:
    """
    Send partial prompt for regeneration and return single string.
    
    Args:
        context: Dictionary containing project context:
            - title: Project title
            - description: Project description
            - old_value: Current value of the section
        section: Section name to regenerate
        instruction: User instruction for regeneration
    
    Returns:
        New text for the section
    """
    client = get_client()
    
    prompt = build_regenerate_section_prompt(context, section, instruction)
    
    model_name = settings.GEMINI_MODEL_NAME
    temperature = settings.GEMINI_TEMPERATURE
    max_tokens = settings.GEMINI_MAX_OUTPUT_TOKENS
    top_p = settings.GEMINI_TOP_P
    top_k = settings.GEMINI_TOP_K
    
    try:
        generation_config = types.GenerateContentConfig(
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_output_tokens=max_tokens,
        )
        
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=generation_config,
        )
        result = response.text
        
        logger.info(f"Successfully regenerated section: {section}")
        return result.strip()
        
    except Exception as e:
        logger.error(f"Error regenerating section: {e}")
        return f"[Error regenerating {section}]: {str(e)}"

