import json
import os
import smtplib
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.message import EmailMessage
import requests


def build_report_from_junit(xml_path: str = "results.xml") -> dict:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    testsuite = root if root.tag == "testsuite" else root.find("testsuite")

    tests = []
    passed = 0
    failed = 0

    for testcase in testsuite.findall("testcase"):
        name = testcase.attrib.get("name", "unknown_test")
        failure = testcase.find("failure")
        error = testcase.find("error")

        if failure is not None or error is not None:
            err_node = failure if failure is not None else error
            msg = err_node.attrib.get("message") or (err_node.text or "").strip()
            tests.append({
                "name": name,
                "result": "FAILED",
                "failure_message": msg,
            })
            failed += 1
        else:
            tests.append({
                "name": name,
                "result": "PASSED",
                "failure_message": None,
            })
            passed += 1

    total = passed + failed
    overall_status = "PASSED" if failed == 0 and total > 0 else "FAILED"

    return {
        "repository": os.getenv("GITHUB_REPOSITORY", "MS-WASAY/devops-lab-mid"),
        "branch": os.getenv("GITHUB_REF_NAME", "main"),
        "commit_sha": os.getenv("GITHUB_SHA", "local"),
        "pipeline_run_id": os.getenv("GITHUB_RUN_ID", "local-run"),
        "execution_timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_status": overall_status,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
        },
        "tests": tests,
    }


def send_to_localhost(report: dict):
    webhook_url = os.getenv("LOCAL_RECEIVER_URL")
    if not webhook_url:
        print("LOCAL_RECEIVER_URL not set, skipping localhost webhook.")
        return
    try:
        resp = requests.post(
            f"{webhook_url.rstrip('/')}/report",
            json=report,
            headers={"X-Pinggy-No-Screen": "true"},
            timeout=15,
        )
        print(f"Localhost delivery status: {resp.status_code}")
    except Exception as e:
        print(f"Failed to send report to localhost: {e}")


def send_email_report(report: dict, report_path: str = "test-report.json"):
    smtp_email = os.getenv("SMTP_EMAIL")
    smtp_password = os.getenv("SMTP_PASSWORD")
    to_email = os.getenv("REPORT_TO_EMAIL")

    if not all([smtp_email, smtp_password, to_email]):
        print("Email secrets not configured, skipping email report.")
        return

    status = report.get("overall_status", "UNKNOWN")
    commit_sha = report.get("commit_sha", "N/A")
    summary = report.get("summary", {})
    tests = report.get("tests", [])

    lines = [
        f"Repository: {report.get('repository')}",
        f"Branch: {report.get('branch')}",
        f"Commit SHA: {commit_sha}",
        f"Pipeline Run ID: {report.get('pipeline_run_id')}",
        f"Timestamp: {report.get('execution_timestamp')}",
        f"Overall Status: {status}",
        "",
        f"Test Counts -> Total: {summary.get('total', 0)}, Passed: {summary.get('passed', 0)}, Failed: {summary.get('failed', 0)}",
        "",
        "Individual Test Results:",
    ]
    for t in tests:
        msg = f" - {t['name']}: {t['result']}"
        if t.get("failure_message"):
            msg += f" (Error: {t['failure_message']})"
        lines.append(msg)

    email_msg = EmailMessage()
    email_msg["Subject"] = f"[CI Report - {status}] {report.get('repository')} ({commit_sha[:7]})"
    email_msg["From"] = smtp_email
    email_msg["To"] = to_email
    email_msg.set_content("\n".join(lines))

    if os.path.exists(report_path):
        with open(report_path, "rb") as f:
            email_msg.add_attachment(
                f.read(),
                maintype="application",
                subtype="json",
                filename="test-report.json",
            )

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(smtp_email, smtp_password)
            smtp.send_message(email_msg)
        print(f"Email report sent successfully to {to_email}")
    except Exception as e:
        print(f"Failed to send email report: {e}")


if __name__ == "__main__":
    report_data = build_report_from_junit("results.xml")
    with open("test-report.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    send_to_localhost(report_data)
    send_email_report(report_data)