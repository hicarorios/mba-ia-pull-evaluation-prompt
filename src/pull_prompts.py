"""Pull de prompts do LangSmith Prompt Hub para arquivos YAML locais."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()

PROMPTS_TO_PULL = [
    {
        "hub_name": "leonanluppi/bug_to_user_story_v1",
        "local_file": "prompts/bug_to_user_story_v1.yml",
        "prompt_key": "bug_to_user_story_v1",
        "description": "Prompt para converter relatos de bugs em User Stories",
        "version": "v1",
        "tags": ["bug-analysis", "user-story", "product-management"],
    }
]


def _extract_messages(prompt_template) -> dict:
    system_prompt = ""
    user_prompt = ""

    messages = getattr(prompt_template, "messages", None) or []

    for message in messages:
        template_obj = getattr(message, "prompt", None)
        template_text = getattr(template_obj, "template", None) if template_obj else None

        if template_text is None:
            template_text = getattr(message, "template", None) or getattr(message, "content", "")

        # Nome da classe é a forma mais estável de identificar o papel da mensagem.
        role = message.__class__.__name__.lower()

        if "system" in role:
            system_prompt = template_text or ""
        elif "human" in role or "user" in role:
            user_prompt = template_text or ""

    # Fallback para prompts que não são ChatPromptTemplate.
    if not system_prompt and not user_prompt:
        fallback_template = getattr(prompt_template, "template", None)
        if fallback_template:
            system_prompt = fallback_template

    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt or "{bug_report}",
    }


def pull_prompts_from_langsmith() -> int:
    saved = 0

    for config in PROMPTS_TO_PULL:
        hub_name = config["hub_name"]
        local_file = config["local_file"]

        print(f"\n→ Pull: {hub_name}")

        try:
            prompt_template = hub.pull(hub_name)
        except Exception as e:
            print(f"   ❌ Falha ao puxar '{hub_name}': {e}")
            continue

        extracted = _extract_messages(prompt_template)

        prompt_payload = {
            config["prompt_key"]: {
                "description": config["description"],
                "system_prompt": extracted["system_prompt"],
                "user_prompt": extracted["user_prompt"],
                "version": config["version"],
                "tags": config["tags"],
                "source": hub_name,
            }
        }

        if save_yaml(prompt_payload, local_file):
            print(f"   ✓ Salvo em: {local_file}")
            saved += 1
        else:
            print(f"   ❌ Não foi possível salvar em {local_file}")

    return saved


def main() -> int:
    print_section_header("PULL DE PROMPTS DO LANGSMITH HUB")

    required_vars = ["LANGSMITH_API_KEY"]
    if not check_env_vars(required_vars):
        return 1

    saved = pull_prompts_from_langsmith()

    print("\n" + "=" * 50)
    if saved == len(PROMPTS_TO_PULL):
        print(f"✅ Todos os {saved} prompts foram baixados com sucesso.")
        print("\nPróximos passos:")
        print("1. Edite prompts/bug_to_user_story_v2.yml com seu prompt otimizado")
        print("2. Execute: python src/push_prompts.py")
        print("3. Execute: python src/evaluate.py")
        return 0

    print(f"⚠️  {saved}/{len(PROMPTS_TO_PULL)} prompts baixados.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
