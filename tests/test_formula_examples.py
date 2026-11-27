"""Format checks for the Phase 0 formula detector test cases."""

from pathlib import Path
from typing import Literal

import pytest
import yaml
from pydantic import BaseModel, model_validator

FIXTURES = Path(__file__).parent / "fixtures"
TEMPLATE = FIXTURES / "formula_examples.template.yaml"
LOCAL = FIXTURES / "formula_examples.local.yaml"


class FormulaExample(BaseModel, extra="forbid"):
    id: str
    placeholder: bool = False
    page_id: str
    page_title: str
    page_version: int
    space: str
    url: str
    section_path: str
    kind: Literal["equation", "calculation_sentence", "table_row"] | None
    text: str
    expected_formula: bool
    note: str | None = None

    @model_validator(mode="after")
    def kind_matches_expectation(self) -> "FormulaExample":
        if self.expected_formula and self.kind is None:
            raise ValueError(f"{self.id}: a formula example needs a kind")
        if not self.expected_formula and self.kind is not None:
            raise ValueError(f"{self.id}: a non-formula example must have kind null")
        return self


class FormulaExamples(BaseModel, extra="forbid"):
    version: Literal[1]
    examples: list[FormulaExample]

    @model_validator(mode="after")
    def ids_are_unique(self) -> "FormulaExamples":
        ids = [example.id for example in self.examples]
        duplicates = {i for i in ids if ids.count(i) > 1}
        if duplicates:
            raise ValueError(f"duplicate example ids: {sorted(duplicates)}")
        return self


def load(path: Path) -> FormulaExamples:
    return FormulaExamples.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def test_template_is_valid_and_all_placeholders():
    examples = load(TEMPLATE).examples
    assert examples
    assert all(example.placeholder for example in examples)


@pytest.mark.skipif(not LOCAL.exists(), reason="formula_examples.local.yaml not present")
def test_local_examples_are_valid():
    examples = load(LOCAL).examples
    real = [example for example in examples if not example.placeholder]
    formulas = [example for example in real if example.expected_formula]
    assert 5 <= len(formulas) <= 10, "Phase 0 needs 5-10 real formula examples"
    assert any(not example.expected_formula for example in real)
    for example in real:
        assert example.url.startswith("https://"), example.id
        assert example.page_version >= 1, example.id
        assert example.text.strip() == example.text and example.text, example.id
