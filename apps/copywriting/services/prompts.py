"""
Prompt templates for AI copywriting generation.

This module contains all prompt templates used for generating and regenerating
copywriting content. Separating prompts makes them easier to maintain and modify.
"""


def build_generate_copywriting_prompt(inputs: dict, search_results: list[dict] = None) -> str:
    """
    Build the main copywriting generation prompt.
    
    Args:
        inputs: Dictionary containing:
            - title: Project title
            - description: Project description
            - platform: Target platform
            - user_description: Optional user note
        search_results: List of selected search results with title and snippet
    
    Returns:
        Formatted prompt string
    """
    user_note = ""
    if inputs.get('user_description'):
        user_note = f"- User Note: {inputs['user_description']}"
    
    # Build search results context
    search_context = ""
    if search_results:
        search_context = "\n\nSelected Search Results (use these as reference for context):\n"
        for idx, result in enumerate(search_results, 1):
            search_context += f"\n{idx}. {result.get('title', 'No title')}\n"
            search_context += f"   {result.get('snippet', 'No description')}\n"
    
    prompt = f"""You are an expert copywriter specialized in SEO and social media. You write engaging, persuasive content in Persian.

Project Information:
- Title: {inputs.get('title', 'Untitled')}
- Description: {inputs.get('description', '')}
- Platform: {inputs.get('platform', 'other')}
{user_note}{search_context}

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

IMPORTANT: Return ONLY a single JSON object (not an array). Do not wrap the response in square brackets. No additional text or explanations."""
    
    return prompt


def build_regenerate_section_prompt(context: dict, section: str, instruction: str) -> str:
    """
    Build the section regeneration prompt.
    
    Args:
        context: Dictionary containing project context:
            - title: Project title
            - description: Project description
            - old_value: Current value of the section
        section: Section name to regenerate
        instruction: User instruction for regeneration
    
    Returns:
        Formatted prompt string
    """
    prompt = f"""You are rewriting one section of a marketing copy in Persian. Follow the user's instructions precisely.

Existing section ({section}): {context.get('old_value', '')}

Goal: {instruction}

Project Context:
- Title: {context.get('title', 'Untitled')}
- Description: {context.get('description', '')}

Return only the new text for this section in Persian. Do not include any explanations or additional text."""
    
    return prompt

