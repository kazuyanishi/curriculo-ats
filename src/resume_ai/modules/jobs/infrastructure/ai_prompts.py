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

Education extraction:
- When category is education, education_requirement may contain only these
  fields: degree_level, field_of_study, institution, and acceptable_statuses.
- Fill each field only when it is explicitly supported by the same literal
  evidence. Do not infer a degree level, field, institution, or status from
  general knowledge or from an ambiguous phrase.
- degree_level may preserve an explicitly stated level such as Bachelor's,
  Master's, Associate, Technical, or Doctorate. Do not convert BSc, BS, BA,
  MSc, or MBA into another label.
- field_of_study and institution must preserve explicitly stated text. Do not
  infer related fields, equivalent degrees, synonyms, or institution quality.
- acceptable_statuses may contain only completed and in_progress. Use
  in_progress only when study in progress is explicit, completed only when
  completion is explicit, both only when both are explicitly accepted, and an
  empty list when status is not specified.
- Do not create an empty education_requirement object. Use null when no field
  can be structured faithfully, when the requirement contains related field or
  another unrepresentable qualifier, or when education is an alternative to
  experience. Never turn education OR experience into two mandatory criteria.
- For every category other than education, education_requirement must be null.

The education_requirement structure does not replace value or evidence. Keep
value as a short readable representation and keep evidence copied verbatim.

Use only these importances: required, preferred, unspecified. Use required only
when the text indicates obligation, preferred only when it indicates preference
or a differentiator, and unspecified when the importance is unclear.
""".strip()


def build_job_criteria_user_prompt(job: JobPosting) -> str:
    return job.description
