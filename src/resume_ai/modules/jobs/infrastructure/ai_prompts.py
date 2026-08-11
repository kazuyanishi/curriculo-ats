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

Category semantics:
- technology includes programming languages, frameworks, libraries, databases,
  platforms, and other technical technologies. Classify Python, Java,
  JavaScript, FastAPI, Django, PostgreSQL, and React as technology.
- language means only human spoken or written languages. Classify English,
  Portuguese, Spanish, and French as language. Do not classify programming
  languages such as Python, Java, or JavaScript as language; classify them as
  technology.
- tool means a tool used in work or development, such as Docker, Git, Jira,
  or Postman.
- skill means a competency or capability, such as communication, problem
  solving, leadership, or customer support. Do not use skill merely because a
  technology requires knowledge.

Preserve education, experience, and certification for their corresponding
requirements. Use other as the fallback when no specific category applies.

Use only these importances: required, preferred, unspecified. Use required only
when the text indicates obligation, preferred only when it indicates preference
or a differentiator, and unspecified when the importance is unclear.
""".strip()


def build_job_criteria_user_prompt(job: JobPosting) -> str:
    return job.description
