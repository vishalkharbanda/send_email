from __future__ import annotations

import argparse
import csv
import os
import smtplib
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import make_msgid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PENDING_CSV = ROOT / "data" / "hr_emails.csv"
SENT_CSV = ROOT / "data" / "sent_emails.csv"
SOFTWARE_RESUME = ROOT / "Vishal_SE_B_Tech.pdf"
DATA_RESUME = ROOT / "Vishal_Data_Engineer.pdf"

PENDING_FIELDS = ["hr_email", "company_name", "job_role"]
SENT_FIELDS = ["hr_email", "company_name", "job_role", "sent_date"]

ROLE_ALIASES = {
    "software": "software engineer",
    "sde": "software engineer",
    "backend": "software engineer",
    "frontend": "software engineer",
    "full stack": "software engineer",
    "fullstack": "software engineer",
    "data": "data engineer",
    "de": "data engineer",
    "ai": "AI engineer",
    "ml": "AI engineer",
    "machine learning": "AI engineer",
    "other": "other",
}


@dataclass(frozen=True)
class SmtpConfig:
    host: str
    port: int
    username: str
    password: str
    from_email: str
    from_name: str


def ensure_csv_files() -> None:
    PENDING_CSV.parent.mkdir(parents=True, exist_ok=True)
    if not PENDING_CSV.exists():
        write_rows(PENDING_CSV, PENDING_FIELDS, [])
    if not SENT_CSV.exists():
        write_rows(SENT_CSV, SENT_FIELDS, [])


def read_rows(path: Path) -> list[dict[str, str]]:
    ensure_csv_files()
    with path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file, skipinitialspace=True)
        rows: list[dict[str, str]] = []
        for raw_row in reader:
            row = {}
            for key, value in raw_row.items():
                if key is None:
                    continue
                row[key.strip()] = (value or "").strip()
            rows.append(row)
        return rows


def write_rows(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def append_rows(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    existing = read_rows(path)
    write_rows(path, fields, existing + rows)


def normalize_role(role: str) -> str:
    cleaned = " ".join(role.strip().lower().replace("_", " ").replace("-", " ").split())
    if not cleaned:
        return "other"
    if cleaned in ROLE_ALIASES:
        return ROLE_ALIASES[cleaned]
    if "software" in cleaned or "developer" in cleaned:
        return "software engineer"
    if "data" in cleaned:
        return "data engineer"
    if cleaned in {"ai engineer", "artificial intelligence engineer"} or "machine learning" in cleaned:
        return "AI engineer"
    return "other"


def normalize_email(email: str) -> str:
    return email.strip()


def is_valid_email(email: str) -> bool:
    email = normalize_email(email)
    return "@" in email and "." in email.rsplit("@", 1)[-1]


def load_smtp_config() -> SmtpConfig:
    required = {
        "SMTP_HOST": os.getenv("SMTP_HOST"),
        "SMTP_USERNAME": os.getenv("SMTP_USERNAME"),
        "SMTP_PASSWORD": os.getenv("SMTP_PASSWORD"),
        "FROM_EMAIL": os.getenv("FROM_EMAIL"),
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    return SmtpConfig(
        host=required["SMTP_HOST"] or "",
        port=int(os.getenv("SMTP_PORT", "587")),
        username=required["SMTP_USERNAME"] or "",
        password=required["SMTP_PASSWORD"] or "",
        from_email=required["FROM_EMAIL"] or "",
        from_name=os.getenv("FROM_NAME", required["FROM_EMAIL"] or "Candidate"),
    )


def profile_summary_for_role(role: str) -> str:
    if role == "software engineer":
        return (
            "I am a Backend Software Engineer with 3.5+ years of experience building Python-based "
            "microservices, REST APIs, automation systems, and production deployments."
        )
    if role == "data engineer":
        return (
            "I am a Data and Backend Engineer with 3.5+ years of experience building ETL/data "
            "pipelines, Python services, real-time processing systems, and analytics-ready datasets."
        )
    if role == "AI engineer":
        return (
            "I am an AI-focused Python engineer with hands-on experience in automation, data "
            "pipelines, backend services, LLM concepts, prompt engineering, and AI-driven workflows."
        )
    return (
        "I am a software and data-focused engineer with 3.5+ years of experience across Python "
        "backend systems, ETL pipelines, automation, APIs, and production operations."
    )


def highlights_for_role(role: str) -> list[str]:
    if role == "software engineer":
        return [
            "Built and maintained scalable Python microservices for Tech Mahindra Device Cloud.",
            "Created REST APIs using Flask/FastAPI and Node.js/Express for real-time device control and data flow.",
            "Improved platform performance by reducing device battery consumption by 35%.",
            "Implemented CI/CD with GitHub Actions, Docker, NGINX deployments, logging, monitoring, and secure release workflows.",
            "Operated and troubleshot distributed backend services across 80+ production servers.",
        ]
    if role == "data engineer":
        return [
            "Built real-time ETL pipelines using Debezium and Azure services, improving data availability and reducing latency.",
            "Worked with Spark, PySpark, Kafka, SQL/NoSQL databases, Azure Synapse, SQL Pool, and Power BI.",
            "Optimized Python regex-based packet parsing pipelines, improving data pipeline efficiency by 40%.",
            "Developed a UPI fraud detection system using ArangoDB and pattern-based anomaly detection.",
            "Streamlined data ingestion and quality processes, reducing integration time by 20%.",
        ]
    if role == "AI engineer":
        return [
            "Built Python automation and data transformation workflows for large-scale raw device packet processing.",
            "Completed Generative AI and AI White Belt certifications covering LLMs, prompt engineering, and AI-driven automation.",
            "Worked on backend services, APIs, structured logging, monitoring, and production deployment workflows.",
            "Applied data engineering skills across ETL, data modeling, anomaly detection, and analytics pipelines.",
            "Comfortable combining Python, data pipelines, and AI concepts to build practical automation and intelligent features.",
        ]
    return [
        "Built Python microservices, REST APIs, ETL pipelines, and automation workflows across software and data projects.",
        "Improved device battery consumption by 35% and data pipeline efficiency by 40% in production systems.",
        "Worked with Flask, FastAPI, Node.js, Docker, GitHub Actions, Azure, AWS, SQL/NoSQL databases, Kafka, and Spark.",
        "Operated distributed services across 80+ production servers using PM2, SSH, logging, and monitoring.",
        "Completed Generative AI and AI White Belt certifications, adding AI automation and LLM fundamentals to my engineering profile.",
    ]


def resume_for_role(role: str) -> Path:
    if role == "software engineer":
        return SOFTWARE_RESUME
    return DATA_RESUME


def display_role(role: str) -> str:
    if role == "other":
        return "software/data engineer"
    return role


def subject_for_role(role: str) -> str:
    if role == "software engineer":
        return "Backend Software Engineer | Python, REST APIs, Microservices"
    if role == "data engineer":
        return "Data Engineer | ETL, Python, Spark, Kafka, Azure"
    if role == "AI engineer":
        return "AI Engineer | Python, Automation, Data Pipelines, GenAI"
    return "Software/Data Engineer | Python, APIs, ETL, Automation"


def attach_resume(message: EmailMessage, resume_path: Path) -> None:
    if not resume_path.exists():
        raise FileNotFoundError(f"Resume not found: {resume_path}")

    with resume_path.open("rb") as file:
        message.add_attachment(
            file.read(),
            maintype="application",
            subtype="pdf",
            filename=resume_path.name,
        )


def build_email(row: dict[str, str], config: SmtpConfig) -> EmailMessage:
    hr_email = normalize_email(row["hr_email"])
    company = row.get("company_name", "").strip()
    role = normalize_role(row.get("job_role", ""))
    target = display_role(role)
    company_phrase = f" at {company}" if company else ""
    resume_link = os.getenv("SOFTWARE_RESUME_LINK" if role == "software engineer" else "DATA_RESUME_LINK", "").strip()
    linkedin_link = os.getenv("LINKEDIN_LINK", "").strip()
    resume_path = resume_for_role(role)

    links = []
    if resume_link:
        links.append(f"Resume: {resume_link}")
    if linkedin_link:
        links.append(f"LinkedIn: {linkedin_link}")

    body = [
        "Hi,",
        "",
        f"I hope you are doing well. I am reaching out to explore {target} opportunities{company_phrase}.",
        "",
        profile_summary_for_role(role),
        "",
        "A few highlights from my experience:",
        *[f"- {highlight}" for highlight in highlights_for_role(role)],
        "",
        f"I have attached my {target} resume for your reference. I would be grateful if you could consider my profile for suitable openings or share it with the relevant hiring team.",
    ]
    if links:
        body.extend(["", *links])
    body.extend(["", "Thank you for your time.", "", f"Regards,", config.from_name])

    message = EmailMessage()
    message["From"] = f"{config.from_name} <{config.from_email}>"
    message["To"] = hr_email
    message["Subject"] = subject_for_role(role)
    message["Message-ID"] = make_msgid(domain=config.from_email.rsplit("@", 1)[-1] if "@" in config.from_email else None)
    message.set_content("\n".join(body))
    attach_resume(message, resume_path)
    return message


def send_email(message: EmailMessage, config: SmtpConfig) -> None:
    with smtplib.SMTP(config.host, config.port, timeout=30) as smtp:
        smtp.starttls()
        smtp.login(config.username, config.password)
        smtp.send_message(message)


def process_emails(limit: int | None, dry_run: bool) -> int:
    ensure_csv_files()
    pending_rows = read_rows(PENDING_CSV)
    sent_rows = read_rows(SENT_CSV)
    already_sent = {normalize_email(row.get("hr_email", "")).lower() for row in sent_rows}

    config = None if dry_run else load_smtp_config()
    remaining_rows: list[dict[str, str]] = []
    newly_sent: list[dict[str, str]] = []
    sent_count = 0
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    for row in pending_rows:
        row = {field: (row.get(field) or "").strip() for field in PENDING_FIELDS}
        row["hr_email"] = normalize_email(row["hr_email"])
        email = row["hr_email"].lower()
        if not is_valid_email(email):
            print(f"Skipping invalid email: {row.get('hr_email', '')}", file=sys.stderr)
            remaining_rows.append(row)
            continue
        if email in already_sent:
            print(f"Already sent earlier, removing from pending: {row['hr_email']}")
            continue
        if limit is not None and sent_count >= limit:
            remaining_rows.append(row)
            continue

        row["job_role"] = normalize_role(row.get("job_role", ""))
        message = build_email(row, config or SmtpConfig("", 587, "", "", "", os.getenv("FROM_NAME", "Candidate")))

        if dry_run:
            print(f"DRY RUN: would send to {row['hr_email']} for {row['job_role']}")
            remaining_rows.append(row)
            continue

        try:
            send_email(message, config)  # type: ignore[arg-type]
        except Exception as exc:
            print(f"Failed to send to {row['hr_email']}: {exc}", file=sys.stderr)
            remaining_rows.append(row)
            continue

        print(f"Sent email to {row['hr_email']}")
        sent_count += 1
        already_sent.add(email)
        newly_sent.append({**row, "sent_date": now})

    if not dry_run:
        write_rows(PENDING_CSV, PENDING_FIELDS, remaining_rows)
        if newly_sent:
            append_rows(SENT_CSV, SENT_FIELDS, newly_sent)

    return sent_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send scheduled HR cold emails from CSV.")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without sending or updating CSV files.")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of emails to send in this run.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sent_count = process_emails(limit=args.limit, dry_run=args.dry_run)
    print(f"Completed. Emails sent: {sent_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
