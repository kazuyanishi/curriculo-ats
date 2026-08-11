from resume_ai.bootstrap import build_extract_job_criteria, build_load_job
from resume_ai.core.config import load_config
from resume_ai.integrations.ai.config import load_ai_config
from resume_ai.modules.jobs.domain.entities import JobCriteria


def run() -> JobCriteria:
    app_config = load_config()
    ai_config = load_ai_config()
    job = build_load_job(app_config).execute()
    return build_extract_job_criteria(ai_config).execute(job)


def main() -> int:
    criteria = run()
    if not criteria.criteria:
        print("No job criteria found.")
        return 0

    for index, criterion in enumerate(criteria.criteria):
        if index:
            print()
        print(f"[{criterion.importance.value}] {criterion.category.value}: {criterion.value}")
        print(f"Evidence: {criterion.evidence}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
