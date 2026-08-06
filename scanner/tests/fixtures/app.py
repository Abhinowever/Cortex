"""Intentionally vulnerable test fixture app for scanner and E2E tests."""

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

fixture_app = FastAPI(title="Vulnerable Test Fixture")


@fixture_app.get("/", response_class=HTMLResponse)
def index():
    return """
    <html>
        <body>
            <h1>Vulnerable Test Target App</h1>
            <ul>
                <li><a href="/search?q=test">Search Page (XSS)</a></li>
                <li><a href="/sqli?id=1">User Query Page (SQLi)</a></li>
                <li><a href="/ssrf?url=http://127.0.0.1:5001/ssrf-callback">Fetch Endpoint (SSRF)</a></li>
                <li><a href="/idor/user/101">Profile Page (IDOR)</a></li>
            </ul>
        </body>
    </html>
    """


@fixture_app.get("/search", response_class=HTMLResponse)
def search(q: str = ""):
    # Intentionally reflected XSS vulnerability
    return f"""
    <html>
        <body>
            <h1>Search Results</h1>
            <p>You searched for: {q}</p>
        </body>
    </html>
    """


@fixture_app.get("/sqli", response_class=HTMLResponse)
def sqli(id: str = ""):
    # Intentionally vulnerable SQLi endpoint returning SQL syntax error
    if "'" in id:
        return "ERROR: You have an error in your SQL syntax near SQLite3.OperationalError"
    return f"User details for ID: {id}"


@fixture_app.get("/ssrf", response_class=HTMLResponse)
def ssrf(url: str = ""):
    # Intentionally vulnerable SSRF endpoint simulating server fetch
    if "ssrf-callback" in url or "169.254.169.254" in url:
        return "fetched_content: ssrf_callback_hit"
    return "fetched_content: normal"


@fixture_app.get("/ssrf-callback")
def ssrf_callback():
    return {"status": "hit", "message": "ssrf_callback_hit"}


@fixture_app.get("/idor/user/{user_id}")
def idor(user_id: int):
    # Intentionally vulnerable IDOR endpoint returning private user data without auth check
    return {"user_id": user_id, "email": f"user{user_id}@example.com", "private_data": "secret_user_info"}


if __name__ == "__main__":
    uvicorn.run(fixture_app, host="127.0.0.1", port=5001)

