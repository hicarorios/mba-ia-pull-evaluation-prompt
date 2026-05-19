"""Testes automatizados para validação do prompt v2 (pytest)."""
import re
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure  # noqa: F401


PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def prompt_data():
    assert PROMPT_FILE.exists(), f"Arquivo não encontrado: {PROMPT_FILE}"
    data = load_prompts(str(PROMPT_FILE))
    assert data is not None, "YAML vazio ou inválido"
    assert PROMPT_KEY in data, f"Chave '{PROMPT_KEY}' não encontrada no YAML"
    return data[PROMPT_KEY]


@pytest.fixture(scope="module")
def prompt_text(prompt_data):
    # Combina system + user em minúsculas para checagens case-insensitive.
    system_prompt = prompt_data.get("system_prompt", "") or ""
    user_prompt = prompt_data.get("user_prompt", "") or ""
    return f"{system_prompt}\n{user_prompt}".lower()


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt_data):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt_data, "Campo 'system_prompt' ausente"
        system_prompt = prompt_data.get("system_prompt")
        assert system_prompt is not None, "Campo 'system_prompt' é None"
        assert isinstance(system_prompt, str), "'system_prompt' deve ser string"
        assert system_prompt.strip() != "", "Campo 'system_prompt' está vazio"

    def test_prompt_has_role_definition(self, prompt_text):
        """Verifica se o prompt define uma persona (ex: 'Você é um Product Manager')."""
        role_patterns = [
            r"voc[eê]\s+[ée]\s+um[a]?",
            r"atue\s+como",
            r"aja\s+como",
            r"you\s+are\s+an?",
        ]

        has_role = any(re.search(pat, prompt_text) for pat in role_patterns)
        assert has_role, (
            "O prompt não define uma persona explícita "
            "(ex: 'Você é um Product Manager')."
        )

    def test_prompt_mentions_format(self, prompt_text):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        format_keywords = [
            "como um",
            "eu quero",
            "para que",
            "critérios de aceitação",
            "given-when-then",
            "dado que",
            "markdown",
            "user story",
        ]

        matches = [kw for kw in format_keywords if kw in prompt_text]
        assert matches, (
            "O prompt não menciona o formato esperado "
            "(Markdown ou padrão de User Story)."
        )

    def test_prompt_has_few_shot_examples(self, prompt_text):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        few_shot_signals = [
            "exemplo 1",
            "exemplo 2",
            "## exemplo",
            "# exemplo",
            "bug report:",
            "resposta:",
            "few-shot",
        ]

        hits = sum(1 for signal in few_shot_signals if signal in prompt_text)
        assert hits >= 2, (
            "O prompt não aparenta conter exemplos Few-shot suficientes "
            "(esperado pelo menos 2 exemplos de entrada/saída)."
        )

    def test_prompt_no_todos(self, prompt_data):
        """Garante que você não esqueceu nenhum [TODO] no texto."""
        system_prompt = prompt_data.get("system_prompt", "") or ""
        user_prompt = prompt_data.get("user_prompt", "") or ""
        combined = f"{system_prompt}\n{user_prompt}"

        assert "[TODO]" not in combined, "Ainda existe '[TODO]' no prompt"
        assert "TODO" not in combined, "Ainda existe 'TODO' no prompt"
        assert "FIXME" not in combined.upper(), "Ainda existe 'FIXME' no prompt"

    def test_minimum_techniques(self, prompt_data):
        """Verifica (pelos metadados do YAML) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt_data.get("techniques_applied", [])
        assert isinstance(techniques, list), (
            "'techniques_applied' deve ser uma lista nos metadados"
        )
        assert len(techniques) >= 2, (
            f"Mínimo de 2 técnicas requeridas; encontradas: {len(techniques)}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
