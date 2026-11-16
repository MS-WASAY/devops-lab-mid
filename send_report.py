import os
import json
import smtplib
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.message import EmailMessage

def parse_junit_xml(xml_path="results.xml"):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    testsuite = root.find("testsuite") if root.tag == "testsuites" else root

    tests = []
    total = int(testsuite.attrib.get("tests", 0))
    failures = int(testsuite.attrib.get("failures", 0))
    errors = int(testsuite.attrib.get("errors", 0))
    failed_count = failures + errors
    passed_count = total - failed_count

    for case in testsuite.findall("testcase"):
        name = case.attrib.get("name")
        failure_node = case.find("failure")
        error_node = case.find("error")
        if failure_node is not None:
            tests.append({"name": name, "result": "FAILED", "failure_message": failure_node.attrib.get("message", "")})
        elif error_node is not None:
            tests.append({"name": name, "result": "FAILED", "failure_message": error_node.attrib.get("message", "")})
        else:
            tests.append({"name": name, "result": "PASSED", "failure_message": None})

    overall_status = "PASSED" if failed_count == 0 and total > 0 else "FAILED"

    return {
        "repository": os.getenv("GITHUB_REPOSITORY", "local/repo"),
        "branch": os.getenv("GITHUB_REF_NAME", "main"),
        "commit_sha": os.getenv("GITHUB_SHA", "local-sha"),
        "pipeline_run_id": os.getenv("GITHUB_RUN_ID", "0"),
        "execution_timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_status": overall_status,
        "summary": {
            "total": total,
            "passed": passed_count,
            "failed": failed_count
        },
        "tests": tests
    }

def send_to_localhost(report):
    webhook_url = os.getenv("LOCAL_RECEIVER_URL")
    if webhook_url:
        try:
            resp = requests.post(f"{webhook_url.rstrip('/')}/report", json=report, timeout=15)
            print("Localhost receiver response:", resp.status_code)
        except Exception as e:
            print("Failed to send to localhost:", e)

def send_email_report(report):
    sender = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    recipient = os.getenv("REPORT_RECIPIENT_EMAIL")
    if not (sender and password and recipient):
        print("Email secrets not configured, skipping email.")
        return

    msg = EmailMessage()
    msg["Subject"] = f"CI Test Report [{report['overall_status']}] - {report['commit_sha'][:7]}"
    msg["From"] = sender
    msg["To"] = recipient

    body = (
        f"Repository: {report['repository']}\n"
        f"Branch: {report['branch']}\n"
        f"Commit SHA: {report['commit_sha']}\n"
        f"Overall Result: {report['overall_status']}\n"
        f"Counts: Total={report['summary']['total']}, Passed={report['summary']['passed']}, Failed={report['summary']['failed']}\n\n"
        f"Details:\n{json.dumps(report['tests'], indent=2)}"
    )
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender, password)
        smtp.send_message(msg)
    print("Email report sent successfully!")

if __name__ == "__main__":
    report_data = parse_junit_xml()
    send_to_localhost(report_data)
    send_email_report(report_data)
