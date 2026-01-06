from flask import Flask, render_template, request, redirect, url_for, send_file, session
import json, os
from collections import Counter

app = Flask(__name__)
app.secret_key = "secret123"

# Data folder and files
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

FILES = {
    "voters": os.path.join(DATA_DIR, "voters.json"),
    "votes": os.path.join(DATA_DIR, "votes.json"),
    "parties": os.path.join(DATA_DIR, "parties.json"),
    "areas": os.path.join(DATA_DIR, "areas.json"),
    "support": os.path.join(DATA_DIR, "support.json")
}

# Utility Functions
def load_data(file):
    if not os.path.exists(file):
        return []
    with open(file, "r") as f:
        try:
            return json.load(f)
        except:
            return []

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

#  Public Routes 
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/castvote", methods=["GET", "POST"])
def cast_vote():
    parties = load_data(FILES["parties"])
    voters = load_data(FILES["voters"])
    votes = load_data(FILES["votes"])

    if request.method == "POST":
        cnic = request.form["cnic"].strip()
        party_name = request.form["party"].strip()

        # Check voter
        voter = next((v for v in voters if v["cnic"] == cnic), None)
        if not voter or voter.get("voted"):
            return render_template("vote_status.html", success=False)

        voter["voted"] = True
        votes.append({
            "cnic": cnic,
            "party": party_name,
            "area": voter["area"]
        })

        save_data(FILES["voters"], voters)
        save_data(FILES["votes"], votes)

        return render_template("vote_status.html", success=True)

    return render_template("cast_vote.html", parties=parties)

# Admin Routes 
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        if username == "admin" and password == "admin":
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    return render_template("admin_dashboard.html")

@app.route("/admin/register-voter", methods=["GET", "POST"])
def register_voter():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    areas = load_data(FILES["areas"])
    voters = load_data(FILES["voters"])

    if request.method == "POST":
        cnic = request.form["cnic"].strip()
        name = request.form["name"].strip()
        area = request.form["area"].strip()

        if any(v["cnic"] == cnic for v in voters):
            return render_template("register_voter.html", areas=areas, error="CNIC already registered")

        voters.append({"cnic": cnic, "name": name, "area": area, "voted": False})
        save_data(FILES["voters"], voters)
        return redirect(url_for("admin_dashboard"))

    return render_template("register_voter.html", areas=areas)

from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/admin/add-party", methods=["GET", "POST"])
def add_party():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    parties = load_data(FILES["parties"])

    if request.method == "POST":
        party_name = (request.form.get("party_name") or "").strip()
        symbol = (request.form.get("symbol") or "").strip()
        founder = (request.form.get("founder") or "").strip()
        leader = (request.form.get("leader") or "").strip()
        year = (request.form.get("year") or "").strip()
        ideology = (request.form.get("ideology") or "").strip()
        head_office = (request.form.get("head_office") or "").strip()
        website = (request.form.get("website") or "").strip()
        description = (request.form.get("description") or "").strip()

        if not party_name or not symbol:
            error = "Party name and symbol are required."
            return render_template("add_party.html", parties=parties, error=error)

        # Handle file upload
        logo_file = request.files.get("logo")
        logo_path = ""
        if logo_file and logo_file.filename != "":
            filename = secure_filename(logo_file.filename)
            logo_file.save(os.path.join(UPLOAD_FOLDER, filename))
            logo_path = f"{UPLOAD_FOLDER}/{filename}" 

        party = {
            "party_name": party_name,
            "symbol": symbol,
            "founder": founder,
            "leader": leader,
            "year": year,
            "ideology": ideology,
            "head_office": head_office,
            "website": website,
            "description": description,
            "logo": logo_path
        }

        parties.append(party)
        save_data(FILES["parties"], parties)

        return redirect(url_for("admin_dashboard"))

    return render_template("add_party.html", parties=parties)



@app.route("/admin/add-area", methods=["GET", "POST"])
def add_area():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    areas = load_data(FILES["areas"])

    if request.method == "POST":
        area = {
            "code": request.form["code"].strip(),
            "area_name": request.form["area_name"].strip(),
            "province": request.form["province"].strip(),
            "type": request.form["type"].strip(),
            "voters": int(request.form["voters"]),
            "remarks": request.form.get("remarks", "").strip()
        }
        areas.append(area)
        save_data(FILES["areas"], areas)
        return redirect(url_for("admin_dashboard"))

    return render_template("add_area.html")

@app.route("/live-results")
def live_results():
    votes = load_data(FILES["votes"])
    results = {}
    for v in votes:
        results[v["party"]] = results.get(v["party"], 0) + 1
    return render_template("live_results.html", results=results)

@app.route("/admin/end-voting")
def end_voting():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    votes = load_data(FILES["votes"])
    area_results = {}

    for v in votes:
        area = v["area"]
        area_results.setdefault(area, {})
        area_results[area][v["party"]] = area_results[area].get(v["party"], 0) + 1

    final_results = {}
    for area, data in area_results.items():
        winner = max(data, key=data.get)
        final_results[area] = {"party": winner, "votes": data[winner]}

    overall = Counter(v["party"] for v in votes).most_common(1)[0][0] if votes else None

    return render_template("end_results.html",
                           area_results=final_results,
                           overall_winner=overall)

# ---------- Download Routes ----------
@app.route("/download/votes")
def download_votes():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    return send_file(FILES["votes"], as_attachment=True)

@app.route("/download/voters")
def download_voters():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    return send_file(FILES["voters"], as_attachment=True)

# ---------- Support ----------
@app.route("/support", methods=["GET", "POST"])
def support():
    support_data = load_data(FILES["support"])
    if request.method == "POST":
        support_data.append({
            "name": request.form["name"].strip(),
            "email": request.form["email"].strip(),
            "issue": request.form["issue"].strip(),
            "message": request.form["message"].strip()
        })
        save_data(FILES["support"], support_data)
        return render_template("support.html", success=True)
    return render_template("support.html", success=False)

# ---------- Run App ----------
if __name__ == "__main__":
    app.run(debug=True, port=8000)
