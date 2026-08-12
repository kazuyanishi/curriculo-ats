from io import BytesIO

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from resume_ai.modules.candidate.domain.entities import Candidate


def _date(value: object) -> str:
    return value.strftime("%Y-%m")


def _text(value: str) -> str:
    return (value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _add_collection(
    story: list[object], styles: object, title: str, items: tuple[object, ...]
) -> None:
    if not items:
        return
    story.append(Paragraph(title, styles["Heading2"]))
    for item in items:
        text = item.name
        if getattr(item, "level", None) is not None:
            text += f" — {item.level.value}"
        if hasattr(item, "issuer"):
            text += f" — {item.issuer}"
        story.append(Paragraph(f"• {_text(text)}", styles["BodyText"]))


class PdfCandidateRenderer:
    def render(self, candidate: Candidate) -> bytes:
        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer,
            rightMargin=0.7 * inch,
            leftMargin=0.7 * inch,
            topMargin=0.7 * inch,
            bottomMargin=0.7 * inch,
        )
        styles = getSampleStyleSheet()
        story: list[object] = [Paragraph(_text(candidate.personal_info.full_name), styles["Title"])]
        contact = [
            candidate.personal_info.city,
            candidate.personal_info.state,
            candidate.personal_info.country,
            candidate.contact_info.email,
            candidate.contact_info.phone,
            candidate.professional_links.linkedin,
            candidate.professional_links.github,
            candidate.professional_links.portfolio,
        ]
        story.append(
            Paragraph(_text(" | ".join(item for item in contact if item)), styles["BodyText"])
        )
        story.append(Spacer(1, 8))

        if candidate.experiences:
            story.append(Paragraph("Experience", styles["Heading2"]))
            for experience in candidate.experiences:
                end_date = _date(experience.end_date) if experience.end_date else "Present"
                dates = f"{_date(experience.start_date)} — {end_date}"
                story.append(
                    Paragraph(
                        _text(f"{experience.role} — {experience.company}"),
                        styles["BodyText"],
                    )
                )
                story.append(Paragraph(_text(dates), styles["BodyText"]))
                for item in (*experience.activities, *experience.achievements):
                    story.append(Paragraph(f"• {_text(item.description)}", styles["BodyText"]))
        if candidate.education:
            story.append(Paragraph("Education", styles["Heading2"]))
            for education in candidate.education:
                dates = " — ".join(
                    _date(value) for value in (education.start_date, education.end_date) if value
                )
                suffix = f" — {dates}" if dates else ""
                story.append(
                    Paragraph(
                        _text(
                            f"{education.course} — {education.institution} — "
                            f"{education.status.value}{suffix}"
                        ),
                        styles["BodyText"],
                    )
                )
        _add_collection(story, styles, "Skills", candidate.skills)
        _add_collection(story, styles, "Technologies", candidate.technologies)
        _add_collection(story, styles, "Tools", candidate.tools)
        _add_collection(story, styles, "Languages", candidate.languages)
        if candidate.certifications:
            story.append(Paragraph("Certifications", styles["Heading2"]))
            for certification in candidate.certifications:
                parts = [certification.name, certification.issuer]
                if certification.issue_date:
                    parts.append(_date(certification.issue_date))
                if certification.expiration_date:
                    parts.append(_date(certification.expiration_date))
                if certification.credential_id:
                    parts.append(certification.credential_id)
                if certification.credential_url:
                    parts.append(certification.credential_url)
                story.append(
                    Paragraph(f"• {_text(' — '.join(parts))}", styles["BodyText"])
                )
        if candidate.projects:
            story.append(Paragraph("Projects", styles["Heading2"]))
            for project in candidate.projects:
                parts = [project.name, project.description, *project.technologies]
                if project.start_date:
                    parts.append(_date(project.start_date))
                if project.end_date:
                    parts.append(_date(project.end_date))
                if project.url:
                    parts.append(project.url)
                story.append(Paragraph(_text(" — ".join(parts)), styles["BodyText"]))

        document.build(story)
        return buffer.getvalue()
