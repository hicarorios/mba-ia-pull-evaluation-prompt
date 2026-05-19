"""Push de prompts otimizados ao LangSmith Prompt Hub (público)."""

import os
import sys
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()

PROMPTS_TO_PUSH = [
    {
        "local_file": "prompts/bug_to_user_story_v2.yml",
        "prompt_key": "bug_to_user_story_v2",
        "hub_short_name": "bug_to_user_story_v2",
    }
]


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    errors = []

    if not isinstance(prompt_data, dict):
        return False, ["Prompt não é um dicionário."]

    system_prompt = (prompt_data.get("system_prompt") or "").strip()
    user_prompt = (prompt_data.get("user_prompt") or "").strip()

    if not system_prompt:
        errors.append("Campo 'system_prompt' vazio ou ausente.")
    if not user_prompt:
        errors.append("Campo 'user_prompt' vazio ou ausente.")

    if "TODO" in system_prompt or "[TODO]" in system_prompt:
        errors.append("O system_prompt ainda contém '[TODO]'.")
    if "TODO" in user_prompt or "[TODO]" in user_prompt:
        errors.append("O user_prompt ainda contém '[TODO]'.")

    techniques = prompt_data.get("techniques_applied") or []
    if len(techniques) < 2:
        errors.append(
            f"É necessário listar no mínimo 2 técnicas em 'techniques_applied' "
            f"(encontradas: {len(techniques)})."
        )

    combined = f"{system_prompt}\n{user_prompt}"
    if "{bug_report}" not in combined:
        errors.append("O placeholder '{bug_report}' precisa estar presente no prompt.")

    return (len(errors) == 0, errors)


def _build_chat_prompt(prompt_data: dict) -> ChatPromptTemplate:
    system_prompt = prompt_data["system_prompt"]
    user_prompt = prompt_data.get("user_prompt") or "{bug_report}"

    return ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", user_prompt),
        ]
    )


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    print(f"\n→ Push: {prompt_name}")

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("   ❌ Prompt inválido:")
        for error in errors:
            print(f"      - {error}")
        return False

    try:
        chat_prompt = _build_chat_prompt(prompt_data)
    except Exception as e:
        print(f"   ❌ Erro ao montar ChatPromptTemplate: {e}")
        return False

    description = prompt_data.get("description", "")
    tags = prompt_data.get("tags", []) or []
    techniques = prompt_data.get("techniques_applied", []) or []

    if techniques:
        techniques_line = "Técnicas aplicadas: " + ", ".join(techniques)
        description = f"{description.strip()}\n\n{techniques_line}" if description else techniques_line

    try:
        # new_repo_is_public=True é exigência do desafio. Description/tags
        # só têm efeito na criação inicial do repo no Hub.
        url = hub.push(
            prompt_name,
            chat_prompt,
            new_repo_is_public=True,
            new_repo_description=(description or None),
            tags=(tags or None),
        )
        print(f"   ✓ Publicado em: {url}")
        return True
    except TypeError:
        # Versões antigas do langchain.hub não aceitam todos os kwargs.
        try:
            url = hub.push(prompt_name, chat_prompt, new_repo_is_public=True)
            print(f"   ✓ Publicado em: {url}")
            print("   ⚠️  Descrição/tags não foram enviadas (versão do LangChain antiga).")
            return True
        except Exception as e:
            print(f"   ❌ Falha ao publicar: {e}")
            return False
    except Exception as e:
        print(f"   ❌ Falha ao publicar: {e}")
        return False


def main() -> int:
    print_section_header("PUSH DE PROMPTS OTIMIZADOS AO LANGSMITH HUB")

    required_vars = ["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]
    if not check_env_vars(required_vars):
        return 1

    username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()

    success = 0
    for config in PROMPTS_TO_PUSH:
        data = load_yaml(config["local_file"])
        if not data:
            print(f"❌ Não foi possível ler {config['local_file']}")
            continue

        prompt_payload = data.get(config["prompt_key"])
        if not prompt_payload:
            print(
                f"❌ Chave '{config['prompt_key']}' não encontrada em "
                f"{config['local_file']}"
            )
            continue

        prompt_name = f"{username}/{config['hub_short_name']}"

        if push_prompt_to_langsmith(prompt_name, prompt_payload):
            success += 1

    print("\n" + "=" * 50)
    if success == len(PROMPTS_TO_PUSH):
        print(f"✅ Todos os {success} prompts foram publicados com sucesso.")
        print("\nPróximo passo: execute a avaliação:")
        print("  python src/evaluate.py")
        return 0

    print(f"⚠️  {success}/{len(PROMPTS_TO_PUSH)} prompts publicados.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
