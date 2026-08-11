from typing import Final

from resume_ai.modules.jobs.domain.entities import JobPosting

JOB_CRITERIA_SYSTEM_PROMPT: Final[str] = """
Extract only job criteria supported by the supplied job description.

Never invent requirements, skills, technologies, tools, languages, education,
experience, or certifications. If no reliable criterion exists, return an
empty criteria collection.

For every criterion, value should be a short representation of the identified
criterion and must not add a requirement unsupported by its evidence.

The evidence MUST be copied verbatim from the supplied job description. Never paraphrase,
summarize, translate, correct, or normalize evidence. Preserve its
exact case, whitespace, and line breaks. The evidence must never be invented.

Use only these categories: skill, technology, tool, language, education,
experience, certification, other.

Use only these importances: required, preferred, unspecified. Use required only
when the text indicates obligation, preferred only when it indicates preference
or a differentiator, and unspecified when the importance is unclear.
""".strip()


def build_job_criteria_user_prompt(job: JobPosting) -> str:
    return job.description
