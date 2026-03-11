import os
import psycopg2
from werkzeug.security import generate_password_hash

DATABASE_URL = os.environ.get("DATABASE_URL", "")
conn = psycopg2.connect(DATABASE_URL)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS admin (
    id SERIAL PRIMARY KEY, username TEXT NOT NULL, password TEXT NOT NULL)''')

c.execute('''CREATE TABLE IF NOT EXISTS profile (
    id SERIAL PRIMARY KEY,
    name TEXT DEFAULT 'Your Name',
    title TEXT DEFAULT 'Full Stack Developer',
    tagline TEXT DEFAULT 'Building digital experiences that matter.',
    bio TEXT DEFAULT 'Write something about yourself here...',
    photo TEXT DEFAULT '',
    blood_group TEXT DEFAULT '',
    email TEXT DEFAULT 'your@email.com',
    phone TEXT DEFAULT '+880 1700 000000',
    location TEXT DEFAULT 'Dhaka, Bangladesh',
    github TEXT DEFAULT '', linkedin TEXT DEFAULT '', twitter TEXT DEFAULT '',
    facebook TEXT DEFAULT '', instagram TEXT DEFAULT '', youtube TEXT DEFAULT '',
    tiktok TEXT DEFAULT '', discord TEXT DEFAULT '', telegram TEXT DEFAULT '',
    whatsapp TEXT DEFAULT '', fiverr TEXT DEFAULT '', upwork TEXT DEFAULT '',
    stackoverflow TEXT DEFAULT '', behance TEXT DEFAULT '', dribbble TEXT DEFAULT '',
    medium TEXT DEFAULT '', hashnode TEXT DEFAULT '',
    website TEXT DEFAULT '', resume TEXT DEFAULT '')''')

c.execute('''CREATE TABLE IF NOT EXISTS education (
    id SERIAL PRIMARY KEY,
    institution TEXT NOT NULL, degree TEXT NOT NULL,
    field TEXT DEFAULT '', duration TEXT DEFAULT '',
    result TEXT DEFAULT '', description TEXT DEFAULT '',
    order_num INTEGER DEFAULT 0)''')

c.execute('''CREATE TABLE IF NOT EXISTS skills (
    id SERIAL PRIMARY KEY, name TEXT NOT NULL,
    level INTEGER DEFAULT 80, category TEXT DEFAULT 'Technical')''')

c.execute('''CREATE TABLE IF NOT EXISTS experience (
    id SERIAL PRIMARY KEY, company TEXT NOT NULL, role TEXT NOT NULL,
    duration TEXT NOT NULL, description TEXT, order_num INTEGER DEFAULT 0)''')

c.execute('''CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY, title TEXT NOT NULL, description TEXT,
    image TEXT DEFAULT '', tags TEXT DEFAULT '',
    link TEXT DEFAULT '', featured BOOLEAN DEFAULT FALSE)''')

c.execute('''CREATE TABLE IF NOT EXISTS achievements (
    id SERIAL PRIMARY KEY, title TEXT NOT NULL, description TEXT,
    year TEXT DEFAULT '', icon TEXT DEFAULT '🏆')''')

c.execute('''CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL,
    subject TEXT, message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, is_read BOOLEAN DEFAULT FALSE)''')

c.execute('''CREATE TABLE IF NOT EXISTS visits (
    id SERIAL PRIMARY KEY,
    ip TEXT DEFAULT '', user_agent TEXT DEFAULT '',
    page TEXT DEFAULT '/',
    visited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

# Seeds
c.execute("SELECT * FROM admin LIMIT 1")
if not c.fetchone():
    c.execute("INSERT INTO admin (username,password) VALUES (%s,%s)",
              ("admin", generate_password_hash("admin123")))

c.execute("SELECT * FROM profile LIMIT 1")
if not c.fetchone():
    c.execute("""INSERT INTO profile (name,title,tagline,bio,email,phone,location)
              VALUES (%s,%s,%s,%s,%s,%s,%s)""",
              ("Your Name","Full Stack Developer",
               "Building digital experiences that matter.",
               "I'm a passionate developer who loves creating modern web applications.",
               "your@email.com","+880 1700 000000","Dhaka, Bangladesh"))

c.execute("SELECT * FROM skills LIMIT 1")
if not c.fetchone():
    c.executemany("INSERT INTO skills (name,level,category) VALUES (%s,%s,%s)", [
        ("Python",90,"Technical"),("Flask",85,"Technical"),
        ("JavaScript",80,"Technical"),("HTML & CSS",92,"Technical"),
        ("SQL",75,"Technical"),("Git",80,"Tools")])

c.execute("SELECT * FROM education LIMIT 1")
if not c.fetchone():
    c.execute("""INSERT INTO education (institution,degree,field,duration,result,order_num)
              VALUES (%s,%s,%s,%s,%s,%s)""",
              ("Your University","Bachelor of Science","Computer Science",
               "2020 - 2024","CGPA 3.8/4.0",1))

conn.commit()
conn.close()
print("✅ PostgreSQL Database ready!")
