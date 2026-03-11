from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os, requests
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import psycopg2
from psycopg2.extras import RealDictCursor

# Cloudinary
import cloudinary
import cloudinary.uploader

app = Flask(__name__)
app.secret_key = "38e9ac7ace3f36a3a82d06218a59df648cac16cdcf2581b7524393d9e66f14bd"

ALLOWED_EXTENSIONS = {'png','jpg','jpeg','gif','webp'}
RECAPTCHA_SECRET   = os.environ.get("RECAPTCHA_SECRET_KEY", "")
RECAPTCHA_SITE     = os.environ.get("RECAPTCHA_SITE_KEY", "")
DATABASE_URL       = os.environ.get("DATABASE_URL", "")

app.config['RECAPTCHA_SITE_KEY'] = RECAPTCHA_SITE

# Cloudinary config
cloudinary.config(
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME", ""),
    api_key    = os.environ.get("CLOUDINARY_API_KEY", ""),
    api_secret = os.environ.get("CLOUDINARY_API_SECRET", ""),
    secure     = True
)

# ── DATABASE ────────────────────────────────────────────────
def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def allowed_file(f):
    return '.' in f and f.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

def upload_image(file):
    if not file or not file.filename or not allowed_file(file.filename):
        return None
    try:
        result = cloudinary.uploader.upload(file, folder="myportfolio")
        return result.get("secure_url")
    except Exception as e:
        print(f"Cloudinary error: {e}")
        return None

def verify_recaptcha(token):
    if not RECAPTCHA_SECRET or not token:
        return True  # skip if not configured
    try:
        r = requests.post("https://www.google.com/recaptcha/api/siteverify", data={
            "secret": RECAPTCHA_SECRET,
            "response": token
        }, timeout=5)
        data = r.json()
        return data.get("success") and data.get("score", 0) >= 0.5
    except:
        return True

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ── PUBLIC ─────────────────────────────────────────────────
@app.route('/')
def index():
    db = get_db(); cur = db.cursor()
    ip = request.remote_addr
    ua = request.user_agent.string[:200]
    cur.execute("INSERT INTO visits (ip, user_agent, page) VALUES (%s,%s,%s)", (ip, ua, '/'))
    db.commit()
    cur.execute("SELECT * FROM profile WHERE id=1")
    profile = cur.fetchone()
    cur.execute("SELECT * FROM skills ORDER BY category, level DESC")
    skills = cur.fetchall()
    cur.execute("SELECT * FROM experience ORDER BY order_num DESC")
    experience = cur.fetchall()
    cur.execute("SELECT * FROM projects ORDER BY featured DESC, id DESC")
    projects = cur.fetchall()
    cur.execute("SELECT * FROM achievements ORDER BY year DESC")
    achievements = cur.fetchall()
    cur.execute("SELECT * FROM education ORDER BY order_num DESC")
    education = cur.fetchall()
    cur.close(); db.close()
    return render_template('index.html',
        profile=profile, skills=skills, experience=experience,
        projects=projects, achievements=achievements, education=education)

@app.route('/contact', methods=['POST'])
def contact():
    name    = request.form.get('name','')
    email   = request.form.get('email','')
    subject = request.form.get('subject','')
    message = request.form.get('message','')
    token   = request.form.get('recaptcha_token','')

    if not verify_recaptcha(token):
        return jsonify({'success': False, 'msg': 'reCAPTCHA verification failed. Please try again.'})

    if name and email and message:
        db = get_db(); cur = db.cursor()
        cur.execute("INSERT INTO messages (name,email,subject,message) VALUES (%s,%s,%s,%s)",
                    (name, email, subject, message))
        db.commit(); cur.close(); db.close()
        return jsonify({'success': True, 'msg': 'Message sent successfully!'})
    return jsonify({'success': False, 'msg': 'Please fill all fields.'})

# ── AUTH ───────────────────────────────────────────────────
@app.route('/login', methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        db = get_db(); cur = db.cursor()
        cur.execute("SELECT * FROM admin WHERE username=%s", (request.form['username'],))
        r = cur.fetchone(); cur.close(); db.close()
        if r and check_password_hash(r['password'], request.form['password']):
            session['admin'] = request.form['username']
            return redirect(url_for('admin_dashboard'))
        error = "Invalid username or password"
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('login'))

@app.route('/reset-password', methods=['GET','POST'])
def reset_password():
    error = success = None
    if request.method == 'POST':
        sk = request.form.get('secret_key')
        np = request.form.get('new_password')
        cp = request.form.get('confirm_password')
        if sk != 'rW0FDcuaJtVbVJZSqkdIqHMkJY0-7YHr': error = "Invalid secret key."
        elif np != cp:          error = "Passwords do not match."
        elif len(np) < 6:       error = "Password must be at least 6 characters."
        else:
            db = get_db(); cur = db.cursor()
            cur.execute("UPDATE admin SET password=%s WHERE id=1", (generate_password_hash(np),))
            db.commit(); cur.close(); db.close()
            success = "Password updated! You can now login."
    return render_template('reset_password.html', error=error, success=success)

# ── ADMIN DASHBOARD ────────────────────────────────────────
@app.route('/admin')
@login_required
def admin_dashboard():
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT * FROM profile WHERE id=1"); profile = cur.fetchone()
    cur.execute("SELECT COUNT(*) as c FROM skills"); skills_count = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM projects"); projects_count = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM experience"); exp_count = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM achievements"); ach_count = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM messages WHERE is_read=false"); unread = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM visits"); total_visits = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM visits WHERE DATE(visited_at)=CURRENT_DATE"); today_visits = cur.fetchone()['c']
    cur.execute("SELECT * FROM messages ORDER BY created_at DESC LIMIT 5"); recent_msgs = cur.fetchall()
    cur.execute("""SELECT DATE(visited_at) as day, COUNT(*) as cnt FROM visits
        WHERE visited_at >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY DATE(visited_at) ORDER BY day""")
    visit_chart_raw = cur.fetchall()
    visit_chart = [{'day': str(row['day']), 'cnt': row['cnt']} for row in visit_chart_raw]
    cur.close(); db.close()
    return render_template('admin/dashboard.html',
        profile=profile, skills_count=skills_count,
        projects_count=projects_count, exp_count=exp_count,
        ach_count=ach_count, unread=unread,
        total_visits=total_visits, today_visits=today_visits,
        recent_msgs=recent_msgs, visit_chart=visit_chart)

# ── PROFILE ────────────────────────────────────────────────
@app.route('/admin/profile', methods=['GET','POST'])
@login_required
def admin_profile():
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT * FROM profile WHERE id=1"); profile = cur.fetchone()
    if request.method == 'POST':
        photo_url = profile['photo']
        if 'photo' in request.files:
            url = upload_image(request.files['photo'])
            if url: photo_url = url
        cur.execute("""UPDATE profile SET
            name=%s,title=%s,tagline=%s,bio=%s,photo=%s,blood_group=%s,
            email=%s,phone=%s,location=%s,
            github=%s,linkedin=%s,twitter=%s,facebook=%s,instagram=%s,
            youtube=%s,tiktok=%s,discord=%s,telegram=%s,whatsapp=%s,
            fiverr=%s,upwork=%s,stackoverflow=%s,behance=%s,dribbble=%s,
            medium=%s,hashnode=%s,website=%s,resume=%s WHERE id=1""",
            (request.form.get('name'), request.form.get('title'),
             request.form.get('tagline'), request.form.get('bio'),
             photo_url, request.form.get('blood_group',''),
             request.form.get('email'), request.form.get('phone'),
             request.form.get('location'),
             request.form.get('github',''), request.form.get('linkedin',''),
             request.form.get('twitter',''), request.form.get('facebook',''),
             request.form.get('instagram',''), request.form.get('youtube',''),
             request.form.get('tiktok',''), request.form.get('discord',''),
             request.form.get('telegram',''), request.form.get('whatsapp',''),
             request.form.get('fiverr',''), request.form.get('upwork',''),
             request.form.get('stackoverflow',''), request.form.get('behance',''),
             request.form.get('dribbble',''), request.form.get('medium',''),
             request.form.get('hashnode',''), request.form.get('website',''),
             request.form.get('resume','')))
        db.commit(); cur.close(); db.close()
        return redirect(url_for('admin_profile'))
    cur.close(); db.close()
    return render_template('admin/profile.html', profile=profile)

# ── EDUCATION ──────────────────────────────────────────────
@app.route('/admin/education', methods=['GET','POST'])
@login_required
def admin_education():
    db = get_db(); cur = db.cursor()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            cur.execute("""INSERT INTO education (institution,degree,field,duration,result,description,order_num)
                VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (request.form['institution'], request.form['degree'],
                 request.form.get('field',''), request.form['duration'],
                 request.form.get('result',''), request.form.get('description',''),
                 request.form.get('order_num',0)))
        elif action == 'delete':
            cur.execute("DELETE FROM education WHERE id=%s", (request.form['id'],))
        db.commit()
    cur.execute("SELECT * FROM education ORDER BY order_num DESC")
    education = cur.fetchall(); cur.close(); db.close()
    return render_template('admin/education.html', education=education)

# ── SKILLS ─────────────────────────────────────────────────
@app.route('/admin/skills', methods=['GET','POST'])
@login_required
def admin_skills():
    db = get_db(); cur = db.cursor()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            cur.execute("INSERT INTO skills (name,level,category) VALUES (%s,%s,%s)",
                        (request.form['name'], request.form['level'], request.form['category']))
        elif action == 'delete':
            cur.execute("DELETE FROM skills WHERE id=%s", (request.form['id'],))
        db.commit()
    cur.execute("SELECT * FROM skills ORDER BY category, level DESC")
    skills = cur.fetchall(); cur.close(); db.close()
    return render_template('admin/skills.html', skills=skills)

# ── EXPERIENCE ─────────────────────────────────────────────
@app.route('/admin/experience', methods=['GET','POST'])
@login_required
def admin_experience():
    db = get_db(); cur = db.cursor()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            cur.execute("""INSERT INTO experience (company,role,duration,description,order_num)
                VALUES (%s,%s,%s,%s,%s)""",
                (request.form['company'], request.form['role'],
                 request.form['duration'], request.form.get('description',''),
                 request.form.get('order_num',0)))
        elif action == 'delete':
            cur.execute("DELETE FROM experience WHERE id=%s", (request.form['id'],))
        db.commit()
    cur.execute("SELECT * FROM experience ORDER BY order_num DESC")
    exp = cur.fetchall(); cur.close(); db.close()
    return render_template('admin/experience.html', experience=exp)

# ── PROJECTS ───────────────────────────────────────────────
@app.route('/admin/projects', methods=['GET','POST'])
@login_required
def admin_projects():
    db = get_db(); cur = db.cursor()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            img_url = ''
            if 'image' in request.files:
                url = upload_image(request.files['image'])
                if url: img_url = url
            cur.execute("INSERT INTO projects (title,description,image,tags,link,featured) VALUES (%s,%s,%s,%s,%s,%s)",
                        (request.form['title'], request.form.get('description',''),
                         img_url, request.form.get('tags',''), request.form.get('link',''),
                         True if request.form.get('featured') else False))
        elif action == 'delete':
            cur.execute("DELETE FROM projects WHERE id=%s", (request.form['id'],))
        db.commit()
    cur.execute("SELECT * FROM projects ORDER BY featured DESC, id DESC")
    projects = cur.fetchall(); cur.close(); db.close()
    return render_template('admin/projects.html', projects=projects)

# ── ACHIEVEMENTS ───────────────────────────────────────────
@app.route('/admin/achievements', methods=['GET','POST'])
@login_required
def admin_achievements():
    db = get_db(); cur = db.cursor()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            cur.execute("INSERT INTO achievements (title,description,year,icon) VALUES (%s,%s,%s,%s)",
                        (request.form['title'], request.form.get('description',''),
                         request.form.get('year',''), request.form.get('icon','🏆')))
        elif action == 'delete':
            cur.execute("DELETE FROM achievements WHERE id=%s", (request.form['id'],))
        db.commit()
    cur.execute("SELECT * FROM achievements ORDER BY year DESC")
    ach = cur.fetchall(); cur.close(); db.close()
    return render_template('admin/achievements.html', achievements=ach)

# ── MESSAGES ───────────────────────────────────────────────
@app.route('/admin/messages')
@login_required
def admin_messages():
    db = get_db(); cur = db.cursor()
    cur.execute("UPDATE messages SET is_read=true"); db.commit()
    cur.execute("SELECT * FROM messages ORDER BY created_at DESC")
    msgs = cur.fetchall(); cur.close(); db.close()
    return render_template('admin/messages.html', messages=msgs)

@app.route('/admin/messages/delete/<int:mid>', methods=['POST'])
@login_required
def delete_message(mid):
    db = get_db(); cur = db.cursor()
    cur.execute("DELETE FROM messages WHERE id=%s", (mid,))
    db.commit(); cur.close(); db.close()
    return redirect(url_for('admin_messages'))

# ── VISITS ─────────────────────────────────────────────────
@app.route('/admin/visits')
@login_required
def admin_visits():
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT COUNT(*) as c FROM visits"); total = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM visits WHERE DATE(visited_at)=CURRENT_DATE"); today = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM visits WHERE visited_at>=CURRENT_DATE - INTERVAL '7 days'"); week = cur.fetchone()['c']
    cur.execute("""SELECT DATE(visited_at) as day, COUNT(*) as cnt FROM visits
        GROUP BY DATE(visited_at) ORDER BY day DESC LIMIT 30""")
    by_day = [{'day': str(row['day']), 'cnt': row['cnt']} for row in cur.fetchall()]
    cur.execute("""SELECT ip, COUNT(*) as cnt FROM visits
        GROUP BY ip ORDER BY cnt DESC LIMIT 20"""); by_ip = cur.fetchall()
    cur.execute("SELECT * FROM visits ORDER BY visited_at DESC LIMIT 50"); recent = cur.fetchall()
    cur.close(); db.close()
    return render_template('admin/visits.html', total=total, today=today, week=week,
        by_day=by_day, by_ip=by_ip, recent=recent)

# ── SETTINGS ───────────────────────────────────────────────
@app.route('/admin/settings', methods=['GET','POST'])
@login_required
def admin_settings():
    success = error = None
    if request.method == 'POST':
        nu = request.form['username']
        np = request.form['password']
        cp = request.form['confirm']
        if np != cp: error = "Passwords do not match"
        else:
            db = get_db(); cur = db.cursor()
            cur.execute("UPDATE admin SET username=%s,password=%s WHERE id=1",
                        (nu, generate_password_hash(np)))
            db.commit(); cur.close(); db.close()
            session['admin'] = nu
            success = "Credentials updated successfully!"
    return render_template('admin/settings.html', success=success, error=error)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host='0.0.0.0', port=port, debug=False)
