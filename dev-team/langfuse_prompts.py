"""Load all system prompts from Langfuse Prompt Management.

Prompt names in Langfuse:
  - ba-prompt         (no template vars)
  - developer-prompt  (no template vars)
  - qa-prompt         (template var: {{max_iterations}})
"""

import logging

from langfuse import Langfuse

logger = logging.getLogger("langfuse_prompts")

_langfuse = Langfuse()


def get_system_prompt(name: str, **variables: str) -> str:
    """Fetch a prompt from Langfuse and compile with template variables."""
    prompt = _langfuse.get_prompt(name, label="production")
    compiled = prompt.compile(**variables)
    logger.info("Loaded prompt '%s' from Langfuse (version %s)", name, prompt.version)
    return compiled
