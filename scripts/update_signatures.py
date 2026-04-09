import json
from pathlib import Path

def update_signatures():
    sig_path = Path("techdetector/signatures.json")
    with open(sig_path, "r") as f:
        data = json.load(f)
        
    techs = data["technologies"]
    
    # Avoid duplicates
    existing_ids = {t["id"] for t in techs}
    
    new_techs = [
        # --- DNS Signatures ---
        {
            "id": "google_workspace", "name": "Google Workspace", "category": "email_provider",
            "detection_vectors": { "dns": { "mx": {"contains": ["google.com", "googlemail.com"]}, "txt": {"contains": ["include:_spf.google.com"]} } }
        },
        {
            "id": "microsoft_365", "name": "Microsoft 365", "category": "email_provider",
            "detection_vectors": { "dns": { "mx": {"contains": ["mail.protection.outlook.com"]}, "txt": {"contains": ["include:spf.protection.outlook.com"]} } }
        },
        {
            "id": "zoho_mail", "name": "Zoho Mail", "category": "email_provider",
            "detection_vectors": { "dns": { "mx": {"contains": ["zoho.com"]}, "txt": {"contains": ["include:zoho.com"]} } }
        },
        {
            "id": "fastmail", "name": "Fastmail", "category": "email_provider",
            "detection_vectors": { "dns": { "mx": {"contains": ["messagingengine.com"]}, "txt": {"contains": ["include:spf.messagingengine.com"]} } }
        },
        {
            "id": "sendgrid", "name": "SendGrid", "category": "email_marketing",
            "detection_vectors": { "dns": { "txt": {"contains": ["include:sendgrid.net"]} } }
        },
        {
            "id": "mailgun", "name": "Mailgun", "category": "email_marketing",
            "detection_vectors": { "dns": { "txt": {"contains": ["include:mailgun.org"]} } }
        },
        {
            "id": "postmark", "name": "Postmark", "category": "email_marketing",
            "detection_vectors": { "dns": { "txt": {"contains": ["include:spf.mtasv.net"]} } }
        },
        {
            "id": "amazon_ses", "name": "Amazon SES", "category": "email_marketing",
            "detection_vectors": { "dns": { "txt": {"contains": ["include:amazonses.com"]} } }
        },
        {
            "id": "proofpoint", "name": "Proofpoint", "category": "email_security",
            "detection_vectors": { "dns": { "mx": {"contains": ["pphosted.com"]}, "txt": {"contains": ["include:spf.proofpoint.com"]} } }
        },
        {
            "id": "mimecast", "name": "Mimecast", "category": "email_security",
            "detection_vectors": { "dns": { "mx": {"contains": ["mimecast.com"]}, "txt": {"contains": ["include:_netblocks.mimecast.com"]} } }
        },
        {
            "id": "barracuda", "name": "Barracuda", "category": "email_security",
            "detection_vectors": { "dns": { "mx": {"contains": ["barracudanetworks.com"]}, "txt": {"contains": ["include:spf.ess.barracudanetworks.com"]} } }
        },
        {
            "id": "aws_route53", "name": "AWS Route53", "category": "dns",
            "detection_vectors": { "dns": { "mx": {"contains": ["awsdns"]} } } # Simplification, NS is better but we query MX/TXT
        },
        
        # --- Job Posting NLP Signatures ---
        {
            "id": "snowflake", "name": "Snowflake", "category": "data_warehouse",
            "detection_vectors": { "job_posting": { "keywords": ["snowflake", "snowflake data cloud"], "context_patterns": ["experience with snowflake", "snowflake expertise"] } }
        },
        {
            "id": "databricks", "name": "Databricks", "category": "data_warehouse",
            "detection_vectors": { "job_posting": { "keywords": ["databricks"], "context_patterns": ["experience with databricks"] } }
        },
        {
            "id": "bigquery", "name": "BigQuery", "category": "data_warehouse",
            "detection_vectors": { "job_posting": { "keywords": ["bigquery", "google bigquery"], "context_patterns": ["experience with bigquery"] } }
        },
        {
            "id": "dbt", "name": "dbt", "category": "data_tools",
            "detection_vectors": { "job_posting": { "keywords": ["dbt models", "dbt cloud", "data build tool"], "context_patterns": ["experience with dbt"] } }
        },
        {
            "id": "airflow", "name": "Apache Airflow", "category": "orchestration",
            "detection_vectors": { "job_posting": { "keywords": ["airflow", "airflow dags"], "context_patterns": ["experience with airflow", "apache airflow"] } }
        },
        {
            "id": "postgresql", "name": "PostgreSQL", "category": "database",
            "detection_vectors": { "job_posting": { "keywords": ["postgresql", "postgres"], "context_patterns": ["experience with postgres"] } }
        },
        {
            "id": "elasticsearch", "name": "Elasticsearch", "category": "database",
            "detection_vectors": { "job_posting": { "keywords": ["elasticsearch"], "context_patterns": ["experience with elasticsearch", "elk stack"] } }
        },
        {
            "id": "github_actions", "name": "GitHub Actions", "category": "ci_cd",
            "detection_vectors": { "job_posting": { "keywords": ["github actions"], "context_patterns": ["ci/cd using github actions"] } }
        },
        {
            "id": "kubernetes", "name": "Kubernetes", "category": "infrastructure",
            "detection_vectors": { "job_posting": { "keywords": ["kubernetes", "k8s"], "context_patterns": ["experience with kubernetes", "managing k8s"] } }
        },
        {
            "id": "docker", "name": "Docker", "category": "infrastructure",
            "detection_vectors": { "job_posting": { "keywords": ["docker"], "context_patterns": ["experience with docker", "containerization"] } }
        },
        {
            "id": "terraform", "name": "Terraform", "category": "infrastructure",
            "detection_vectors": { "job_posting": { "keywords": ["terraform"], "context_patterns": ["experience with terraform", "infrastructure as code"] } }
        },
        {
            "id": "aws", "name": "AWS", "category": "cloud",
            "detection_vectors": { "job_posting": { "keywords": ["aws", "amazon web services"], "context_patterns": ["experience with aws"] } }
        },
        {
            "id": "gcp", "name": "GCP", "category": "cloud",
            "detection_vectors": { "job_posting": { "keywords": ["gcp", "google cloud platform"], "context_patterns": ["experience with gcp"] } }
        },
        {
            "id": "datadog_nlp", "name": "Datadog", "category": "monitoring",
            "detection_vectors": { "job_posting": { "keywords": ["datadog"], "context_patterns": ["monitoring with datadog"] } }
        },
        {
            "id": "pagerduty", "name": "PagerDuty", "category": "monitoring",
            "detection_vectors": { "job_posting": { "keywords": ["pagerduty"], "context_patterns": ["on-call via pagerduty"] } }
        },
        {
            "id": "okta", "name": "Okta", "category": "security",
            "detection_vectors": { "job_posting": { "keywords": ["okta"], "context_patterns": ["identity management with okta"] } }
        },
        {
            "id": "slack", "name": "Slack", "category": "communication",
            "detection_vectors": { "job_posting": { "keywords": ["slack"], "context_patterns": ["communication via slack"] } }
        },
        {
            "id": "ruby", "name": "Ruby", "category": "language",
            "detection_vectors": { "job_posting": { "keywords": ["ruby", "ruby on rails"], "context_patterns": ["experience with ruby"] } }
        },
        {
            "id": "go", "name": "Go", "category": "language",
            "detection_vectors": { "job_posting": { "keywords": ["golang", "go programming"], "context_patterns": ["experience with go", "experience with golang"] } }
        }
    ]
    
    for nt in new_techs:
        if nt["id"] not in existing_ids:
            techs.append(nt)
            
    with open(sig_path, "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    update_signatures()
