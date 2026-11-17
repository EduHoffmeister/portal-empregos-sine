import os
import secrets
from datetime import datetime
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", ""),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
    PERMANENT_SESSION_LIFETIME=60 * 60 * 8,
)

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH", "")

if not app.config["SECRET_KEY"]:
    raise RuntimeError("Configure SECRET_KEY no ambiente antes de iniciar o sistema.")
if not ADMIN_PASSWORD_HASH:
    raise RuntimeError("Configure ADMIN_PASSWORD_HASH no ambiente antes de iniciar o sistema.")



def get_connection():
    return psycopg.connect(
        os.environ["DATABASE_URL"],
        row_factory=dict_row
    )


def read_jobs():
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM vagas"
        ).fetchall()



def write_jobs(jobs):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM vagas")

            cur.executemany(
                """
                INSERT INTO vagas (
                    id, title, quantity, company, location,
                    description, requirements, education,
                    experience, schedule, salary, published_at, status
                )
                VALUES (
                    %(id)s, %(title)s, %(quantity)s, %(company)s,
                    %(location)s, %(description)s, %(requirements)s,
                    %(education)s, %(experience)s, %(schedule)s,
                    %(salary)s, %(published_at)s, %(status)s
                )
                """,
                jobs
            )



def csrf_token():
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_urlsafe(32)
    return session["_csrf_token"]


app.jinja_env.globals["csrf_token"] = csrf_token


@app.before_request
def protect_post_requests():
    if request.method == "POST":
        sent = request.form.get("_csrf_token", "")
        saved = session.get("_csrf_token", "")
        if not saved or not secrets.compare_digest(sent, saved):
            abort(400, description="A sessão do formulário expirou. Atualize a página e tente novamente.")


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def clean(value, limit=5000):
    return (value or "").strip()[:limit]


def job_from_form(existing=None):
    existing = existing or {}
    title = clean(request.form.get("title"), 120)
    if not title:
        raise ValueError("Informe o nome do cargo.")
    try:
        quantity = int(request.form.get("quantity", "1"))
    except ValueError:
        raise ValueError("A quantidade de vagas deve ser um número.")
    if not 1 <= quantity <= 999:
        raise ValueError("A quantidade deve estar entre 1 e 999.")

    return {
        "id": existing.get("id") or secrets.token_hex(8),
        "title": title,
        "quantity": quantity,
        "company": clean(request.form.get("company"), 120),
        "location": clean(request.form.get("location"), 160),
        "description": clean(request.form.get("description"), 5000),
        "requirements": clean(request.form.get("requirements"), 3000),
        "education": clean(request.form.get("education"), 160),
        "experience": clean(request.form.get("experience"), 160),
        "schedule": clean(request.form.get("schedule"), 160),
        "salary": clean(request.form.get("salary"), 100),
        "published_at": existing.get("published_at") or datetime.now().strftime("%d/%m/%Y"),
        "status": clean(request.form.get("status"), 20) or "ativa",
    }


@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


@app.route("/")
def home():
    jobs = [j for j in read_jobs() if j.get("status") == "ativa"]
    query = clean(request.args.get("q"), 100).casefold()
    if query:
        jobs = [
            j for j in jobs
            if query in " ".join([
                j.get("title", ""), j.get("description", ""),
                j.get("requirements", ""), j.get("location", ""),
                j.get("company", "")
            ]).casefold()
        ]
    jobs.sort(key=lambda j: j.get("id", ""), reverse=True)
    return render_template("home.html", jobs=jobs, query=request.args.get("q", ""))


@app.route("/vaga/<job_id>")
def job_detail(job_id):
    job = next((j for j in read_jobs() if j.get("id") == job_id and j.get("status") == "ativa"), None)
    if not job:
        abort(404)
    return render_template("job_detail.html", job=job)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        username = clean(request.form.get("username"), 80)
        password = request.form.get("password", "")
        if secrets.compare_digest(username, ADMIN_USERNAME) and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session.clear()
            session["admin_logged_in"] = True
            session.permanent = True
            flash("Acesso autorizado. Bem-vindo ao painel.", "success")
            return redirect(url_for("admin_dashboard"))
        flash("Usuário ou senha inválidos.", "error")
    return render_template("admin_login.html")


@app.route("/admin/logout", methods=["POST"])
@admin_required
def admin_logout():
    session.clear()
    flash("Você saiu do painel administrativo.", "success")
    return redirect(url_for("home"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    jobs = read_jobs()
    jobs.sort(key=lambda j: j.get("id", ""), reverse=True)
    return render_template("admin_dashboard.html", jobs=jobs)


@app.route("/admin/vagas/nova", methods=["GET", "POST"])
@admin_required
def new_job():
    if request.method == "POST":
        try:
            job = job_from_form()
            jobs = read_jobs()
            jobs.append(job)
            write_jobs(jobs)
            flash("Vaga publicada com sucesso.", "success")
            return redirect(url_for("admin_dashboard"))
        except ValueError as e:
            flash(str(e), "error")
    return render_template("job_form.html", job=None, page_title="Cadastrar vaga")


@app.route("/admin/vagas/<job_id>/editar", methods=["GET", "POST"])
@admin_required
def edit_job(job_id):
    jobs = read_jobs()
    job = next((j for j in jobs if j.get("id") == job_id), None)
    if not job:
        abort(404)
    if request.method == "POST":
        try:
            updated = job_from_form(job)
            jobs = [updated if j.get("id") == job_id else j for j in jobs]
            write_jobs(jobs)
            flash("Vaga atualizada.", "success")
            return redirect(url_for("admin_dashboard"))
        except ValueError as e:
            flash(str(e), "error")
    return render_template("job_form.html", job=job, page_title="Editar vaga")


@app.route("/admin/vagas/<job_id>/status", methods=["POST"])
@admin_required
def toggle_job_status(job_id):
    jobs = read_jobs()
    found = False
    for job in jobs:
        if job.get("id") == job_id:
            job["status"] = "encerrada" if job.get("status") == "ativa" else "ativa"
            found = True
            break
    if not found:
        abort(404)
    write_jobs(jobs)
    flash("Status da vaga atualizado.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/vagas/<job_id>/excluir", methods=["POST"])
@admin_required
def delete_job(job_id):
    jobs = read_jobs()
    filtered = [j for j in jobs if j.get("id") != job_id]
    if len(filtered) == len(jobs):
        abort(404)
    write_jobs(filtered)
    flash("Vaga excluída.", "success")
    return redirect(url_for("admin_dashboard"))


@app.errorhandler(400)
def bad_request(error):
    return render_template("error.html", code=400, message=getattr(error, "description", "Solicitação inválida.")), 400


@app.errorhandler(404)
def not_found(error):
    return render_template("error.html", code=404, message="A página ou vaga que você procura não foi encontrada."), 404


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=os.environ.get("FLASK_DEBUG", "0") == "1")
