# engine/validator.py
# Input validation for JD and candidate data


def validate_jd(jd: dict) -> dict:
    """
    Ensure JD has minimum required fields.
    Fills defaults for missing optional fields.
    """
    # Must have at least a role or some skills
    has_role = bool(jd.get("role") and jd["role"] != "Not Specified")
    has_skills = bool(jd.get("required_skills"))

    if not has_role and not has_skills:
        raise ValueError(
            "JD must contain at least a role title or required skills. "
            "Please provide a more detailed job description."
        )

    # Fill defaults for optional fields
    jd.setdefault("role", "Not Specified")
    jd.setdefault("required_skills", [])
    jd.setdefault("preferred_skills", [])
    jd.setdefault("tools", [])
    jd.setdefault("experience_min", 0)
    jd.setdefault("experience_max", 100)
    jd.setdefault("responsibilities", [])
    jd.setdefault("ownership_level", "Medium")
    jd.setdefault("domain", "General")

    return jd


def validate_candidate(candidate: dict) -> dict:
    """
    Ensure candidate has minimum required fields.
    Fills defaults for missing optional fields.
    """
    if not candidate.get("name"):
        raise ValueError("Candidate must have a name.")

    # Fill defaults
    candidate.setdefault("skills", [])
    candidate.setdefault("tools", [])
    candidate.setdefault("experience", 0)
    candidate.setdefault("ownership", "basic")
    candidate.setdefault("projects", [])
    candidate.setdefault("confidence", 0)

    return candidate


def validate_candidates(candidates: list) -> list:
    """Validate all candidates. Returns only valid ones."""
    if not candidates:
        raise ValueError(
            "No candidates could be parsed. Please check the input format. "
            "Expected format: 'Candidate 1:\\nName: ...\\nSkills:\\n...'"
        )

    validated = []
    errors = []

    for i, c in enumerate(candidates):
        try:
            validated.append(validate_candidate(c))
        except ValueError as e:
            errors.append(f"Candidate {i + 1}: {str(e)}")

    if not validated:
        raise ValueError(
            f"All candidates failed validation:\n" +
            "\n".join(errors)
        )

    return validated