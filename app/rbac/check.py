"""Concept-level RBAC against YAML allowed_roles."""

from __future__ import annotations

from app.semantic import ConceptNotFoundError, get_concepts


class AccessDeniedError(PermissionError):
    """Raised when the caller's role may not use a concept."""

    def __init__(self, concept: str, role: str) -> None:
        self.concept = concept
        self.role = role
        super().__init__(f"Access denied for role '{role}' on concept '{concept}'")


def assert_allowed(concept_name: str, role: str) -> None:
    """
    Ensure role is in the concept's allowed_roles.

    Raises:
        ConceptNotFoundError: unknown concept
        AccessDeniedError: role not permitted
    """
    concepts = get_concepts()
    concept = concepts.get(concept_name)
    if concept is None:
        raise ConceptNotFoundError(f"Unknown concept: {concept_name}")
    if role not in concept.allowed_roles:
        raise AccessDeniedError(concept_name, role)
