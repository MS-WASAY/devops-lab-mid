import re
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, HttpUrl, ValidationError, field_validator
from typing import List

app = FastAPI(title="Assignment Submission Portal")
submissions: List[dict] = []

REG_NO_PATTERN = re.compile(r"^(SP|FA)\d{2}-[A-Z]{2,4}-\d{3}$", re.IGNORECASE)

class SubmissionSchema(BaseModel):
    name: str
    reg_no: str
    title: str
    url: HttpUrl

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str):
        if not v or not v.strip():
            raise ValueError("Missing required field: Student Name is required.")
        return v.strip()

    @field_validator("reg_no")
    @classmethod
    def validate_reg_no(cls, v: str):
        if not v or not v.strip():
            raise ValueError("Missing required field: Registration Number is required.")
        cleaned = v.strip().upper()
        if not REG_NO_PATTERN.match(cleaned):
            raise ValueError("Invalid Registration Number format. Expected format: SP23-BCS-043")
        return cleaned

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str):
        if not v or not v.strip():
            raise ValueError("Missing required field: Assignment Title is required.")
        return v.strip()

    @field_validator("url", mode="before")
    @classmethod
    def validate_url_not_empty(cls, v: str):
        if not v or not str(v).strip():
            raise ValueError("Missing required field: Submission URL is required.")
        return str(v).strip()


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>CUI Assignment Portal</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 720px; margin: 40px auto; padding: 20px; background: #f8fafc; }}
        .card {{ background: #ffffff; padding: 25px 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); }}
        h2 {{ color: #17365d; margin-top: 0; }}
        label {{ font-weight: bold; display: block; margin-top: 10px; }}
        input {{ width: 100%; padding: 10px; margin: 6px 0 12px; box-sizing: border-box; border: 1px solid #cbd5e1; border-radius: 5px; }}
        button {{ padding: 11px 22px; background: #0056b3; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; margin-top: 6px; }}
        button:hover {{ background: #004494; }}
        .error {{ background: #fee2e2; color: #991b1b; border: 1px solid #f87171; padding: 12px 15px; border-radius: 6px; margin-bottom: 16px; font-weight: 500; }}
        .success {{ background: #dcfce7; color: #166534; border: 1px solid #4ade80; padding: 12px 15px; border-radius: 6px; margin-bottom: 16px; font-weight: 500; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background: #f1f5f9; }}
    </style>
</head>
<body>
    <div class="card">
        <h2>COMSATS Assignment Submission Portal</h2>
        {message_html}
        <form method="post" action="/submit">
            <label>Student Name *</label>
            <input type="text" name="name" placeholder="Ali Khan">
            <label>Registration Number *</label>
            <input type="text" name="reg_no" placeholder="SP23-BCS-043">
            <label>Assignment Title *</label>
            <input type="text" name="title" placeholder="DevOps Lab Mid">
            <label>Submission URL *</label>
            <input type="text" name="url" placeholder="https://github.com/user/repo">
            <button type="submit">Submit Assignment</button>
        </form>
        <h3>Saved Submissions</h3>
        <table>
            <tr><th>Name</th><th>Reg No</th><th>Title</th><th>URL</th></tr>
            {rows_html}
        </table>
    </div>
</body>
</html>
"""

def render_page(error: str = "", success: str = ""):
    message_html = ""
    if error:
        message_html = f'<div class="error">{error}</div>'
    elif success:
        message_html = f'<div class="success">{success}</div>'

    rows_html = "".join(
        f"<tr><td>{s['name']}</td><td>{s['reg_no']}</td><td>{s['title']}</td><td><a href='{s['url']}' target='_blank'>{s['url']}</a></td></tr>"
        for s in submissions
    )
    return HTML_TEMPLATE.format(message_html=message_html, rows_html=rows_html)

@app.get("/", response_class=HTMLResponse)
def home():
    return render_page()

@app.post("/submit")
def submit_assignment(
    name: str = Form(""),
    reg_no: str = Form(""),
    title: str = Form(""),
    url: str = Form("")
):
    try:
        valid_data = SubmissionSchema(name=name, reg_no=reg_no, title=title, url=url)
        record = {
            "name": valid_data.name,
            "reg_no": valid_data.reg_no,
            "title": valid_data.title,
            "url": str(valid_data.url)
        }
        submissions.append(record)
        return HTMLResponse(
            content=render_page(success="Assignment Submitted Successfully!"),
            status_code=200
        )
    except ValidationError as e:
        first_err = e.errors()[0]
        field = first_err["loc"][0]
        raw_msg = first_err["msg"].replace("Value error, ", "")

        if field == "url" and "Missing required field" not in raw_msg:
            error_msg = "Invalid Submission URL. Please enter a valid URL starting with http:// or https://"
        else:
            error_msg = raw_msg

        return HTMLResponse(content=render_page(error=f"Validation Error: {error_msg}"), status_code=400)

@app.get("/api/submissions")
def get_submissions():
    return JSONResponse(content=submissions)