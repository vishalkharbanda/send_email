# Cold Email Scheduler

This repo sends scheduled HR cold emails from a CSV list and moves successfully sent rows into a sent-history CSV.

## Files

- `data/hr_emails.csv`: Add HR contacts here from your phone and push to Git.
- `data/sent_emails.csv`: The pipeline appends successfully sent contacts here.
- `src/send_cold_emails.py`: Sends emails and updates both CSV files.
- `.github/workflows/send-cold-emails.yml`: Runs every day at 8:00 AM IST.
- `Vishal_SE_B_Tech.pdf`: Attached for software engineer roles.
- `Vishal_Data_Engineer.pdf`: Attached for data engineer, AI engineer, and other roles.

## Pending CSV Format

Edit `data/hr_emails.csv`:

```csv
hr_email,company_name,job_role
hr@example.com,Acme,software engineer
recruiter@example.com,,data engineer
jobs@example.com,Future AI,AI engineer
people@example.com,Startup,other
```

`hr_email` is required. `company_name` is optional. `job_role` can be:

- `software engineer`
- `data engineer`
- `AI engineer`
- `other`

For `other`, the email uses a software + data engineering mixed profile.

## Resume Attachment Rules

- `software engineer`: attaches `Vishal_SE_B_Tech.pdf`.
- `data engineer`: attaches `Vishal_Data_Engineer.pdf`.
- `AI engineer`: attaches `Vishal_Data_Engineer.pdf`.
- `other`: attaches `Vishal_Data_Engineer.pdf` and uses a mixed software/data email format.

The email body is automatically formatted differently for each profile type.

## GitHub Secrets

Add these repository secrets in GitHub:

- `SMTP_HOST`: SMTP server, for example `smtp.gmail.com`
- `SMTP_PORT`: SMTP port, usually `587`
- `SMTP_USERNAME`: Your email username
- `SMTP_PASSWORD`: Your app password
- `FROM_EMAIL`: Sender email address
- `FROM_NAME`: Sender display name, for example your full name
- `SOFTWARE_RESUME_LINK`: Optional public link for your software engineer resume.
- `DATA_RESUME_LINK`: Optional public link for your data/AI engineer resume.
- `LINKEDIN_LINK`: LinkedIn profile URL

For Gmail, use an App Password instead of your normal password.

## Run Locally

Dry run without sending:

```powershell
python src/send_cold_emails.py --dry-run
```

Send for real:

```powershell
python src/send_cold_emails.py
```

Limit the number of emails in one run:

```powershell
python src/send_cold_emails.py --limit 10
```

## How It Works

1. Add rows to `data/hr_emails.csv`.
2. Push the change to GitHub.
3. GitHub Actions runs every day at 8:00 AM IST.
4. Successfully emailed rows are removed from `data/hr_emails.csv`.
5. The same details plus `sent_date` are appended to `data/sent_emails.csv`.
6. GitHub Actions commits the CSV updates back to the repo.
