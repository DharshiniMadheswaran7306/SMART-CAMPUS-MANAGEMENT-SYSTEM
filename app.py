"""
Smart Campus Management System – app.py
Orders can be placed ANY time; delivery happens only during break windows.
Staff see all orders on the Admin Canteen dashboard.
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3, smtplib, json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = "smart_campus_secret_key_2026"
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0   # disable CSS/JS caching in dev

EMAIL_SENDER   = "xxyyzz@gmail.com"
EMAIL_PASSWORD = "aabbccdd"
SMTP_SERVER    = "smtp.gmail.com"
SMTP_PORT      = 587

# Delivery is only during these windows (ordering is always allowed)
BREAK_TIMES = [
    ("10:45", "11:05"),
    ("12:05", "13:00"),
    ("14:45", "15:00"),
]

# ─── DB helpers ───────────────────────────────
def get_db():
    db = sqlite3.connect("smart_campus.db")
    db.row_factory = sqlite3.Row
    return db

def is_break_time():
    now = datetime.now().strftime("%H:%M")
    return any(s <= now <= e for s, e in BREAK_TIMES)

def get_next_break():
    now = datetime.now().strftime("%H:%M")
    for s, e in BREAK_TIMES:
        if now < s:
            return (s, e)
    return None

def send_email_to_all_students(subject, body):
    """Send HTML email to every student. Prints detailed status to console."""

    # ── Guard: skip if credentials are still placeholders ──
    if "your_email" in EMAIL_SENDER or "your_app_password" in EMAIL_PASSWORD:
        print("⚠️  EMAIL NOT SENT: Please set EMAIL_SENDER and EMAIL_PASSWORD in app.py")
        print("   See README.md → 'Enable Emails' section for step-by-step instructions.")
        return

    db = get_db()
    students = db.execute("SELECT email FROM students").fetchall()
    db.close()

    sent, failed = 0, 0
    print(f"📧 Sending '{subject}' to {len(students)} student(s)…")

    for row in students:
        to_addr = row["email"]
        try:
            msg = MIMEMultipart("alternative")
            msg["From"]    = EMAIL_SENDER
            msg["To"]      = to_addr
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "html"))

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as srv:
                srv.ehlo()
                srv.starttls()
                srv.ehlo()
                srv.login(EMAIL_SENDER, EMAIL_PASSWORD)
                srv.sendmail(EMAIL_SENDER, to_addr, msg.as_string())

            print(f"   ✅ Sent to {to_addr}")
            sent += 1

        except smtplib.SMTPAuthenticationError:
            print(f"   ❌ AUTH FAILED for {to_addr}")
            print("      → Gmail is rejecting your password.")
            print("      → You need a Gmail APP PASSWORD, not your normal password.")
            print("      → Go to: myaccount.google.com → Security → 2-Step → App Passwords")
            failed += 1
            break   # No point retrying — all will fail with same credentials

        except smtplib.SMTPException as e:
            print(f"   ❌ SMTP error for {to_addr}: {e}")
            failed += 1

        except Exception as e:
            print(f"   ❌ Unexpected error for {to_addr}: {e}")
            failed += 1

    print(f"📧 Done — {sent} sent, {failed} failed.")


def send_test_email(to_addr):
    """Test email function — called from /admin/test_email route."""
    errors = []

    if "your_email" in EMAIL_SENDER:
        errors.append("EMAIL_SENDER is still the placeholder. Open app.py and set your Gmail address.")
    if "your_app_password" in EMAIL_PASSWORD:
        errors.append("EMAIL_PASSWORD is still the placeholder. You need a Gmail App Password (not your normal password).")

    if errors:
        return False, "\n".join(errors)

    try:
        msg = MIMEMultipart("alternative")
        msg["From"]    = EMAIL_SENDER
        msg["To"]      = to_addr
        msg["Subject"] = "✅ Smart Campus – Email Test"
        msg.attach(MIMEText(
            "<h2>Email is working!</h2>"
            "<p>Your Smart Campus email notifications are configured correctly.</p>"
            "<p style='color:#999;font-size:12px;'>© 2026 Smart Campus Management System</p>",
            "html"
        ))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as srv:
            srv.ehlo(); srv.starttls(); srv.ehlo()
            srv.login(EMAIL_SENDER, EMAIL_PASSWORD)
            srv.sendmail(EMAIL_SENDER, to_addr, msg.as_string())

        return True, f"Test email sent to {to_addr} ✅"

    except smtplib.SMTPAuthenticationError:
        return False, (
            "Gmail rejected the password.\n"
            "You must use a Gmail APP PASSWORD — not your normal Gmail password.\n"
            "Steps: Google Account → Security → 2-Step Verification → App Passwords → "
            "Select app: Mail, Select device: Windows → Generate → copy the 16-char code."
        )
    except smtplib.SMTPConnectError:
        return False, "Could not connect to Gmail. Check your internet connection."
    except Exception as e:
        return False, f"Error: {e}"

# ─── DB init ──────────────────────────────────
def init_db():
    db = get_db(); c = db.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
        name TEXT NOT NULL, register_number TEXT NOT NULL,
        department TEXT NOT NULL, classroom TEXT NOT NULL, email TEXT NOT NULL)""")

    c.execute("""CREATE TABLE IF NOT EXISTS attendance(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL, date TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'present')""")

    c.execute("""CREATE TABLE IF NOT EXISTS events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, category TEXT NOT NULL, description TEXT,
        event_date TEXT NOT NULL, event_time TEXT NOT NULL, venue TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")

    c.execute("""CREATE TABLE IF NOT EXISTS menu_items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, category TEXT NOT NULL, meal_time TEXT NOT NULL,
        price REAL DEFAULT 0, stock INTEGER DEFAULT 100, available INTEGER DEFAULT 1)""")

    c.execute("""CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL, item_id INTEGER NOT NULL,
        quantity INTEGER DEFAULT 1,
        order_date TEXT DEFAULT CURRENT_DATE, order_time TEXT DEFAULT CURRENT_TIME,
        delivery_block TEXT DEFAULT '', delivery_class TEXT DEFAULT '',
        payment_mode TEXT DEFAULT 'cash',
        order_ref TEXT DEFAULT '', special_note TEXT DEFAULT '',
        status TEXT DEFAULT 'pending')""")

    c.execute("""CREATE TABLE IF NOT EXISTS credit_points(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER UNIQUE NOT NULL,
        points INTEGER DEFAULT 0, free_meals_earned INTEGER DEFAULT 0)""")

    # Seed students
    c.execute("SELECT COUNT(*) FROM students")
    if c.fetchone()[0] == 0:
        rows = [
            # ── UPDATE THESE EMAILS to real addresses before going live ──
            ("STU001","pass123","Dharshini",   "21CS001","CSE",         "303", EMAIL_SENDER),
            ("STU002","pass123","Priya Sharma", "21EC002","Electronics", "201", EMAIL_SENDER),
            ("STU003","pass123","Rahul Singh",  "21ME003","Mechanical",  "101", EMAIL_SENDER),
        ]
        c.executemany("INSERT INTO students(user_id,password,name,register_number,department,classroom,email) VALUES(?,?,?,?,?,?,?)", rows)
        c.execute("SELECT id FROM students")
        for r in c.fetchall():
            c.execute("INSERT OR IGNORE INTO credit_points(student_id,points) VALUES(?,0)", (r[0],))

    # Seed attendance
    c.execute("SELECT COUNT(*) FROM attendance")
    if c.fetchone()[0] == 0:
        import random
        from datetime import timedelta
        c.execute("SELECT id FROM students")
        for sid in [r[0] for r in c.fetchall()]:
            for off in range(30):
                d = date.today() - timedelta(days=off)
                if d.weekday() < 5:
                    st = "absent" if random.random() < 0.15 else "present"
                    c.execute("INSERT OR IGNORE INTO attendance(student_id,date,status) VALUES(?,?,?)",(sid,str(d),st))

    # Seed menu
    c.execute("SELECT COUNT(*) FROM menu_items")
    if c.fetchone()[0] == 0:
        menu = [
            ("Apple Juice","Fresh Juice","morning",30,100),("Orange Juice","Fresh Juice","morning",30,100),
            ("Pineapple Juice","Fresh Juice","morning",30,100),("Watermelon Juice","Fresh Juice","morning",25,100),
            ("Pomegranate Juice","Fresh Juice","morning",40,100),("Muskmelon Juice","Fresh Juice","morning",30,100),
            ("Vanilla Shake","Milkshakes","morning",40,100),("Strawberry Shake","Milkshakes","morning",45,100),
            ("Mango Shake","Milkshakes","morning",45,100),("Pistachio Shake","Milkshakes","morning",50,100),
            ("Blackcurrant Shake","Milkshakes","morning",45,100),("Oreo Shake","Milkshakes","morning",55,100),
            ("Kitkat Shake","Milkshakes","morning",55,100),
            ("Samosa","Chat Items","morning",15,100),("Egg Puffs","Chat Items","morning",20,100),
            ("Veg Puffs","Chat Items","morning",15,100),("Mushroom Puffs","Chat Items","morning",20,100),
            ("Pepsi","Soft Drinks","morning",30,100),("Coke","Soft Drinks","morning",30,100),
            ("Mirinda","Soft Drinks","morning",30,100),("Slice","Soft Drinks","morning",30,100),
            ("Frooti","Soft Drinks","morning",25,100),
            ("Pongal","Tiffin","morning",40,100),("Dosa","Tiffin","morning",35,100),
            ("Vadai","Tiffin","morning",20,100),("Idli","Tiffin","morning",30,100),
            ("Puri","Tiffin","morning",35,100),
            ("Chicken Biryani","Rice & Mains","lunch_dinner",80,100),
            ("Chicken Rice","Rice & Mains","lunch_dinner",70,100),
            ("Veg Rice","Rice & Mains","lunch_dinner",50,100),
            ("Mushroom Rice","Rice & Mains","lunch_dinner",60,100),
            ("Parota","Rice & Mains","lunch_dinner",40,100),
            ("Curd Rice","Rice & Mains","lunch_dinner",40,100),
            ("Tomato Rice","Rice & Mains","lunch_dinner",45,100),
            ("Dosa (Lunch)","Rice & Mains","lunch_dinner",35,100),
            ("Chicken 65","Rice & Mains","lunch_dinner",90,100),
        ]
        c.executemany("INSERT INTO menu_items(name,category,meal_time,price,stock) VALUES(?,?,?,?,?)", menu)

    # ── Always fix fake placeholder emails on startup ──
    # If any student still has a @college.edu address, replace it with EMAIL_SENDER
    # so email notifications actually reach someone
    if "your_email" not in EMAIL_SENDER:
        c.execute("""
            UPDATE students
            SET email = ?
            WHERE email LIKE '%@college.edu' OR email LIKE '%@example.com'
        """, (EMAIL_SENDER,))
        rows_fixed = c.rowcount
        if rows_fixed:
            print(f"📧 Auto-fixed {rows_fixed} student email(s) → {EMAIL_SENDER}")

    db.commit(); db.close()
    print("✅ DB ready.")

# ─── Auth ─────────────────────────────────────
@app.route("/", methods=["GET","POST"])
def login():
    if "student_id" in session:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        uid = request.form.get("user_id","").strip()
        pwd = request.form.get("password","").strip()
        db  = get_db()
        stu = db.execute("SELECT * FROM students WHERE user_id=? AND password=?",(uid,pwd)).fetchone()
        db.close()
        if stu:
            session["student_id"]   = stu["id"]
            session["student_name"] = stu["name"]
            flash(f"Welcome, {stu['name']}! 👋","success")
            return redirect(url_for("dashboard"))
        flash("Invalid credentials.","error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.","info")
    return redirect(url_for("login"))

# ─── Student pages ────────────────────────────
@app.route("/dashboard")
def dashboard():
    if "student_id" not in session: return redirect(url_for("login"))
    sid = session["student_id"]; db = get_db()
    stu     = db.execute("SELECT * FROM students WHERE id=?",(sid,)).fetchone()
    total   = db.execute("SELECT COUNT(*) FROM attendance WHERE student_id=?",(sid,)).fetchone()[0]
    absents = db.execute("SELECT COUNT(*) FROM attendance WHERE student_id=? AND status='absent'",(sid,)).fetchone()[0]
    presents = total - absents
    att_pct  = round((presents/total*100) if total else 0, 1)
    events   = db.execute("SELECT * FROM events ORDER BY created_at DESC LIMIT 3").fetchall()
    cp       = db.execute("SELECT points FROM credit_points WHERE student_id=?",(sid,)).fetchone()
    points   = cp["points"] if cp else 0
    tod_ord  = db.execute("SELECT COUNT(*) FROM orders WHERE student_id=? AND order_date=?",(sid,str(date.today()))).fetchone()[0]
    db.close()
    return render_template("dashboard.html", student=stu, att_pct=att_pct,
        presents=presents, absents=absents, events=events, points=points, today_orders=tod_ord)

@app.route("/profile")
def profile():
    if "student_id" not in session: return redirect(url_for("login"))
    db = get_db(); stu = db.execute("SELECT * FROM students WHERE id=?",(session["student_id"],)).fetchone(); db.close()
    return render_template("profile.html", student=stu)

@app.route("/attendance")
def attendance():
    if "student_id" not in session: return redirect(url_for("login"))
    sid = session["student_id"]; db = get_db()
    recs    = db.execute("SELECT date,status FROM attendance WHERE student_id=? ORDER BY date",(sid,)).fetchall()
    total   = len(recs); absents = sum(1 for r in recs if r["status"]=="absent")
    presents = total - absents
    att_pct  = round((presents/total*100) if total else 0, 1)
    db.close()
    return render_template("attendance.html",
        att_dict=json.dumps({r["date"]:r["status"] for r in recs}),
        presents=presents, absents=absents, att_pct=att_pct, total=total)

@app.route("/events")
def events():
    if "student_id" not in session: return redirect(url_for("login"))
    db = get_db(); evs = db.execute("SELECT * FROM events ORDER BY event_date DESC").fetchall(); db.close()
    return render_template("events.html", events=evs)

@app.route("/credits")
def credits():
    if "student_id" not in session: return redirect(url_for("login"))
    sid = session["student_id"]; db = get_db()
    cp  = db.execute("SELECT * FROM credit_points WHERE student_id=?",(sid,)).fetchone()
    pts = cp["points"] if cp else 0; fm = cp["free_meals_earned"] if cp else 0
    ords = db.execute("""SELECT o.order_date,o.order_time,m.name,m.price
        FROM orders o JOIN menu_items m ON o.item_id=m.id
        WHERE o.student_id=? ORDER BY o.order_date DESC,o.order_time DESC LIMIT 20""",(sid,)).fetchall()
    db.close()
    return render_template("credits.html", points=pts, free_meals=fm, orders=ords,
        next_milestone=100-(pts%100) if pts%100 else 100)

# ─── Canteen – browse (any time) ──────────────
@app.route("/canteen")
def canteen():
    if "student_id" not in session: return redirect(url_for("login"))
    db = get_db(); items = db.execute("SELECT * FROM menu_items ORDER BY meal_time,category,name").fetchall(); db.close()
    morning = {}; lunch_dinner = {}
    for item in items:
        cat = item["category"]
        (morning if item["meal_time"]=="morning" else lunch_dinner).setdefault(cat,[]).append(item)
    return render_template("canteen.html",
        morning=morning, lunch_dinner=lunch_dinner,
        in_break=is_break_time(), break_times=BREAK_TIMES)

# ─── Checkout – cart ▶ details ▶ payment ──────
@app.route("/canteen/checkout", methods=["GET","POST"])
def checkout():
    if "student_id" not in session: return redirect(url_for("login"))
    sid = session["student_id"]; db = get_db()
    student = db.execute("SELECT * FROM students WHERE id=?",(sid,)).fetchone()

    if request.method == "POST":
        cart_json    = request.form.get("cart_data","[]")
        payment_mode = request.form.get("payment_mode","cash")
        block        = request.form.get("block","").strip()
        class_no     = request.form.get("class_no","").strip()
        special_note = request.form.get("special_note","").strip()

        try:
            cart = json.loads(cart_json)
        except Exception:
            flash("Cart error. Try again.","error"); db.close(); return redirect(url_for("canteen"))
        if not cart:
            flash("Cart is empty!","error"); db.close(); return redirect(url_for("canteen"))

        now       = datetime.now()
        order_ref = f"ORD{now.strftime('%Y%m%d%H%M%S')}{sid}"
        total_amount = 0; order_items = []; ok = True

        for entry in cart:
            iid = entry.get("id"); qty = int(entry.get("qty",1))
            mi  = db.execute("SELECT * FROM menu_items WHERE id=?",(iid,)).fetchone()
            if not mi: continue
            if mi["stock"] < qty:
                flash(f"'{mi['name']}' only has {mi['stock']} left.","error"); ok=False; continue

            for _ in range(qty):
                db.execute("""INSERT INTO orders
                    (student_id,item_id,quantity,order_date,order_time,
                     delivery_block,delivery_class,payment_mode,order_ref,special_note,status)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                    (sid,iid,1,str(date.today()),now.strftime("%H:%M:%S"),
                     block,class_no,payment_mode,order_ref,special_note,"pending"))

            db.execute("UPDATE menu_items SET stock=stock-? WHERE id=?",(qty,iid))
            if mi["stock"]-qty <= 0:
                db.execute("UPDATE menu_items SET available=0 WHERE id=?",(iid,))

            db.execute("""INSERT INTO credit_points(student_id,points) VALUES(?,?)
                ON CONFLICT(student_id) DO UPDATE SET points=points+?""",(sid,5*qty,5*qty))

            lt = mi["price"]*qty; total_amount+=lt
            order_items.append({"name":mi["name"],"qty":qty,"price":mi["price"],"total":lt})

        if not ok:
            db.rollback(); db.close(); return redirect(url_for("canteen"))

        cp = db.execute("SELECT points FROM credit_points WHERE student_id=?",(sid,)).fetchone()
        if cp and cp["points"]%100==0 and cp["points"]>0:
            db.execute("UPDATE credit_points SET free_meals_earned=free_meals_earned+1 WHERE student_id=?",(sid,))

        db.commit(); db.close()
        return render_template("order_success.html",
            student=student, order_items=order_items, total_amount=total_amount,
            order_ref=order_ref, payment_mode=payment_mode,
            block=block, class_no=class_no, special_note=special_note,
            in_break=is_break_time(), next_break=get_next_break(), break_times=BREAK_TIMES)

    db.close()
    return render_template("checkout.html", student=student, in_break=is_break_time())

# ─── API: item list for JS ────────────────────
@app.route("/api/menu_items")
def api_menu_items():
    db = get_db(); items = db.execute("SELECT id,name,price,stock,available FROM menu_items").fetchall(); db.close()
    return jsonify([dict(i) for i in items])

# ─── Admin – events ───────────────────────────
@app.route("/admin/events", methods=["GET","POST"])
def admin_events():
    if request.method == "POST":
        title,category,description = request.form["title"],request.form["category"],request.form.get("description","")
        event_date,event_time,venue = request.form["event_date"],request.form["event_time"],request.form["venue"]
        db = get_db()
        db.execute("INSERT INTO events(title,category,description,event_date,event_time,venue) VALUES(?,?,?,?,?,?)",
                   (title,category,description,event_date,event_time,venue)); db.commit(); db.close()
        # Email notification — wrapped so a bad SMTP config never prevents saving
        try:
            body = (f"<html><body style='font-family:Arial;'>"
                    f"<h2 style='color:#4f46e5;'>📅 New Event: {title}</h2>"
                    f"<p><b>Category:</b> {category}</p>"
                    f"<p><b>Date & Time:</b> {event_date} at {event_time}</p>"
                    f"<p><b>Venue:</b> {venue}</p>"
                    f"<p><b>Description:</b> {description}</p>"
                    f"<hr><p style='color:#999;font-size:12px;'>© 2026 Smart Campus Management System</p>"
                    f"</body></html>")
            send_email_to_all_students(f"📅 New Event: {title}", body)
            flash(f"Event '{title}' added! Email sent to all students. ✅","success")
        except Exception as mail_err:
            print(f"Email error (event saved OK): {mail_err}")
            flash(f"Event '{title}' added! ⚠️ Email not sent — check SMTP settings in app.py.","success")
        return redirect(url_for("admin_events"))
    db = get_db(); evs = db.execute("SELECT * FROM events ORDER BY created_at DESC").fetchall(); db.close()
    return render_template("admin_events.html", events=evs)

@app.route("/admin/delete_event/<int:eid>")
def delete_event(eid):
    db = get_db(); db.execute("DELETE FROM events WHERE id=?",(eid,)); db.commit(); db.close()
    flash("Event deleted.","info"); return redirect(url_for("admin_events"))

# ─── Admin – canteen orders + restock ─────────
@app.route("/admin/canteen")
def admin_canteen():
    db = get_db()
    rows = db.execute("""
        SELECT o.id, o.order_ref, o.order_time, o.delivery_block, o.delivery_class,
               o.payment_mode, o.special_note, o.status, o.order_date, o.quantity,
               s.name AS student_name, s.department, s.classroom AS profile_class,
               m.name AS item_name, m.price
        FROM orders o
        JOIN students s ON o.student_id=s.id
        JOIN menu_items m ON o.item_id=m.id
        WHERE o.order_date=?
        ORDER BY o.order_time DESC""",(str(date.today()),)).fetchall()

    groups = {}
    for row in rows:
        ref = row["order_ref"] or str(row["id"])
        if ref not in groups:
            groups[ref] = {
                "ref": ref, "time": row["order_time"][:5],
                "student_name": row["student_name"], "department": row["department"],
                "delivery_block": row["delivery_block"] or "—",
                "delivery_class": row["delivery_class"] or row["profile_class"],
                "payment_mode": row["payment_mode"],
                "special_note": row["special_note"] or "—",
                "status": row["status"], "order_lines": [], "total": 0,
            }
        groups[ref]["order_lines"].append({"name":row["item_name"],"qty":row["quantity"],"price":row["price"]})
        groups[ref]["total"] += row["price"]*row["quantity"]

    items = db.execute("SELECT * FROM menu_items ORDER BY meal_time,category").fetchall()
    db.close()
    return render_template("admin_canteen.html",
        order_groups=list(groups.values()), items=items,
        in_break=is_break_time(), break_times=BREAK_TIMES)

@app.route("/admin/order_status/<ref>/<status>")
def update_order_status(ref, status):
    if status not in ("preparing","ready","delivered"):
        flash("Invalid status.","error"); return redirect(url_for("admin_canteen"))
    db = get_db(); db.execute("UPDATE orders SET status=? WHERE order_ref=?",(status,ref)); db.commit(); db.close()
    flash(f"Order marked as '{status}'.","success"); return redirect(url_for("admin_canteen"))

@app.route("/admin/restock/<int:iid>")
def restock_item(iid):
    db = get_db(); item = db.execute("SELECT * FROM menu_items WHERE id=?",(iid,)).fetchone()
    if item:
        db.execute("UPDATE menu_items SET stock=100,available=1 WHERE id=?",(iid,))
        db.commit(); flash(f"'{item['name']}' restocked ✅","success")
    db.close(); return redirect(url_for("admin_canteen"))

# ─── Admin – Update Student Emails ───────────
@app.route("/admin/student_emails", methods=["GET", "POST"])
def student_emails():
    """Admin: update student email addresses directly from browser."""
    db = get_db()
    if request.method == "POST":
        students = db.execute("SELECT id, name FROM students").fetchall()
        updated = 0
        for stu in students:
            field_key = f"email_{stu['id']}"
            new_email = request.form.get(field_key, "").strip()
            if new_email:
                db.execute("UPDATE students SET email=? WHERE id=?", (new_email, stu["id"]))
                updated += 1
        db.commit()
        db.close()
        flash(f"✅ Updated {updated} student email(s) successfully!", "success")
        return redirect(url_for("student_emails"))

    students = db.execute("SELECT id, name, user_id, department, email FROM students").fetchall()
    db.close()
    return render_template("student_emails.html", students=students, sender=EMAIL_SENDER)


# ─── Admin – Email Test ───────────────────────
@app.route("/admin/test_email", methods=["GET", "POST"])
def test_email():
    """Admin page to verify email config works before relying on it."""
    result = None
    if request.method == "POST":
        to_addr = request.form.get("to_addr", "").strip()
        if not to_addr:
            result = {"ok": False, "msg": "Please enter a recipient email address."}
        else:
            ok, msg = send_test_email(to_addr)
            result = {"ok": ok, "msg": msg}
    return render_template("test_email.html",
        sender=EMAIL_SENDER,
        password_set="your_app_password" not in EMAIL_PASSWORD and "your_email" not in EMAIL_SENDER,
        result=result)


# ─── Jinja2 globals & filters ─────────────────
# Must be outside __main__ so they work when Flask is run via "flask run" or directly
app.jinja_env.globals["enumerate"] = enumerate   # usable as {{ enumerate(...) }}
app.jinja_env.filters["enumerate"] = enumerate   # usable as {{ list | enumerate }}


# ─── Always initialise DB when module loads ────
# Runs whether you use "python app.py" or Flask's reloader
with app.app_context():
    init_db()

# ─── Run ──────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=5000)
