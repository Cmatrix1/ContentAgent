"""
AI client for generating copywriting using Google Generative AI.
"""
import json
import logging
from typing import Dict

from django.conf import settings
from google import genai
from google.genai import types


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


def generate_copywriting(inputs: dict) -> dict:
    """
    Send structured prompt to LLM and return JSON output.
    
    Args:
        inputs: Dictionary containing:
            - title: Project title
            - description: Project description
            - platform: Target platform
            - user_description: Optional user note
    
    Returns:
        Dictionary with generated copywriting sections
    """
    client = get_client()
    
    user_note = ""
    if inputs.get('user_description'):
        user_note = f"- User Note: {inputs['user_description']}"
    
    prompt = f"""You are an expert copywriter specialized in SEO and social media. You write engaging, persuasive content in Persian.

Project Information:
- Title: {inputs.get('title', 'Untitled')}
- Description: {inputs.get('description', '')}
- Platform: {inputs.get('platform', 'other')}
{user_note}

Generate marketing texts in Persian for this content in JSON format with the following structure:
{{
  "title": "engaging title",
  "caption": "detailed caption for social media",
  "micro_caption": "short version of caption",
  "meta_description": "SEO-optimized meta description",
  "hashtags": ["hashtag1", "hashtag2", "hashtag3"],
  "cta": "call to action text",
  "alt_text": "alternative text for accessibility"
}}

Return ONLY the JSON, no additional text."""
    
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
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
    
    prompt = f"""You are rewriting one section of a marketing copy in Persian. Follow the user's instructions precisely.

Existing section ({section}): {context.get('old_value', '')}

Goal: {instruction}

Project Context:
- Title: {context.get('title', 'Untitled')}
- Description: {context.get('description', '')}

Return only the new text for this section in Persian. Do not include any explanations or additional text."""
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        result = response.text
        
        logger.info(f"Successfully regenerated section: {section}")
        return result.strip()
        
    except Exception as e:
        logger.error(f"Error regenerating section: {e}")
        return f"[Error regenerating {section}]: {str(e)}"

