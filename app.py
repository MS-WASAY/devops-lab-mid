from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, HttpUrl, ValidationError, field_validator
from typing import List

app = FastAPI(title="Assignment Submission Portal")
submissions: List[dict] = []

class SubmissionSchema(BaseModel):
    name: str
    reg_no: str = "DEFAULT"
    title: str
    url: HttpUrl

    @field_validator("name", "reg_no", "title")
    @classmethod
    def not_empty(cls, v: str):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>CUI Assignment Portal</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 700px; margin: 40px auto; padding: 20px; }}
        input {{ width: 100%; padding: 8px; margin: 6px 0 15px; box-sizing: border-box; }}
        button {{ padding: 10px 20px; background: #0056b3; color: white; border: none; cursor: pointer; }}
        .error {{ color: red; margin-bottom: 15px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    </style>
</head>
<body>
    <h2>COMSATS Assignment Submission Portal</h2>
    {error_html}
    <form method="post" action="/submit">
        <label>Student Name *</label>
        <input type="text" name="name" placeholder="Ali Khan">
        <label>Registration Number *</label>
        <input type="text" name="reg_no" placeholder="FA23-BCS-001">
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
</body>
</html>
"""

def render_page(error: str = ""):
    error_html = f'<div class="error">{error}</div>' if error else ""
    rows_html = "".join(
        f"<tr><td>{s['name']}</td><td>{s['reg_no']}</td><td>{s['title']}</td><td><a href='{s['url']}'>{s['url']}</a></td></tr>"
        for s in submissions
    )
    return HTML_TEMPLATE.format(error_html=error_html, rows_html=rows_html)

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
        return HTMLResponse(content=render_page(), status_code=200)
    except ValidationError as e:
        return HTMLResponse(content=render_page(error=f"Validation Error: {e.errors()[0]['msg']}"), status_code=400)

@app.get("/api/submissions")
def get_submissions():
    return JSONResponse(content=submissions)
