from flask import Flask, render_template, request, redirect, url_for, session
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import imagehash
from PIL import Image
import uuid
from sentence_transformers import SentenceTransformer, util
import numpy as np
import json
import qrcode

# Load the pre-trained model once when the app starts
text_model = SentenceTransformer('all-MiniLM-L6-v2')

app = Flask(__name__)
# IMPORTANT: Change this to a long, random string for security
app.secret_key = "your_super_secret_and_random_key" 
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['QR_CODE_FOLDER'] = 'static/qrcodes'

# --- DATABASE CONNECTION ---
def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        db_password = os.environ.get('DB_PASSWORD')
        if not db_password:
            print("WARNING: Database password not set in environment variables. Using fallback.")
            db_password = "Suja@2006" 
            
        conn = psycopg2.connect(
            host="db.eiulinywwfkmfnmjwwyn.supabase.co",
            database="postgres",
            user="postgres",
            password=db_password,
            port=5432
        )
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

# --- AI & NOTIFICATION HELPER FUNCTIONS ---
def compute_image_embedding(filepath):
    """Computes a perceptual hash (embedding) for an image file."""
    try:
        img = Image.open(filepath)
        hash_val = imagehash.phash(img)
        return str(hash_val)
    except Exception as e:
        print(f"Could not compute hash for {filepath}: {e}")
        return None

def compute_text_embedding(text):
    """Computes a vector embedding for a string of text."""
    try:
        embedding = text_model.encode(text)
        return json.dumps(embedding.tolist())
    except Exception as e:
        print(f"Could not compute text embedding: {e}")
        return None

def hamming_distance(hash1, hash2):
    """Calculates the similarity distance between two image hashes."""
    return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))

def create_notification_for_match(conn, new_found_item_id):
    """Checks a new found item against all lost items using multimodal matching."""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT image_embedding, text_embedding FROM found_items WHERE id = %s", (new_found_item_id,))
    found_item = cursor.fetchone()
    if not found_item: return

    found_img_hash = found_item.get('image_embedding')
    found_text_emb_str = found_item.get('text_embedding')
    if not found_img_hash or not found_text_emb_str: return

    found_text_emb = np.array(json.loads(found_text_emb_str))

    cursor.execute("SELECT id, user_id, image_embedding, text_embedding FROM lost_items WHERE status = 'Pending'")
    lost_items = cursor.fetchall()

    for lost_item in lost_items:
        lost_img_hash = lost_item.get('image_embedding')
        lost_text_emb_str = lost_item.get('text_embedding')
        if not lost_img_hash or not lost_text_emb_str: continue

        # Calculate scores safely
        try:
            distance = hamming_distance(found_img_hash, lost_img_hash)
            image_score = (64 - distance) / 64
            lost_text_emb = np.array(json.loads(lost_text_emb_str))
            text_score = util.cos_sim(found_text_emb, lost_text_emb).item()
        except:
            continue # Skip if embeddings are invalid

        # Combine scores
        final_score = (0.4 * image_score) + (0.6 * text_score)

        if final_score > 0.75:
            message = f"A strong match for your lost item was found (Score: {final_score:.0%})! Click to review."
            cursor.execute(
                "INSERT INTO notifications (user_id, message) VALUES (%s, %s)",
                (lost_item['user_id'], message)
            )
            
    conn.commit()
    cursor.close()

# --- CORE APP ROUTES ---
@app.route('/')
def home():
    """Displays the main dashboard for logged-in users."""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    if not conn: return "Error: Could not connect to the database."
        
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT COUNT(*) as unread_count FROM notifications WHERE user_id = %s AND is_read = FALSE", (session['user_id'],))
    notification_count = cursor.fetchone()['unread_count']

    cursor.execute("SELECT li.*, c.name as category_name FROM lost_items li JOIN categories c ON li.category_id = c.id WHERE li.user_id = %s ORDER BY li.created_at DESC;", (session['user_id'],))
    lost_items = cursor.fetchall()
    
    cursor.execute("SELECT fi.*, c.name as category_name, u.username as reported_by FROM found_items fi JOIN categories c ON fi.category_id = c.id JOIN users u ON fi.user_id = u.id ORDER BY fi.created_at DESC LIMIT 10;")
    found_items = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('home.html', username=session['username'], lost_items=lost_items, found_items=found_items, notification_count=notification_count)

@app.route('/report/<item_type>', methods=['GET', 'POST'])
def report_item(item_type):
    """Handles the form for reporting a lost or found item."""
    if 'user_id' not in session: return redirect(url_for('login'))
    if item_type not in ['lost', 'found']: return "Invalid page", 404

    conn = get_db_connection()
    if not conn: return "Error: Could not connect to the database."
        
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM categories ORDER BY name;")
    categories = cursor.fetchall()
    
    if request.method == 'POST':
        file = request.files.get('file')
        if not (file and file.filename):
            return "File is required.", 400

        original_filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{original_filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)

        embedding = compute_image_embedding(filepath)
        description = request.form['description']
        text_emb = compute_text_embedding(description)
        
        if item_type == 'found':
            qr_token = str(uuid.uuid4())
            claim_url = url_for('claim_via_qr', token=qr_token, _external=True)
            qr_img = qrcode.make(claim_url)
            qr_code_filename = f"{qr_token}.png"
            
            # Use app.static_folder for a reliable absolute path to save the file
            full_qr_path = os.path.join(app.config['QR_CODE_FOLDER'], qr_code_filename)
            os.makedirs(os.path.dirname(full_qr_path), exist_ok=True)
            qr_img.save(full_qr_path)
            
            # Use a relative path for the database and URL
            qr_code_path = os.path.join('static', 'qrcodes', qr_code_filename).replace("\\", "/")

            sql = "INSERT INTO found_items (user_id, category_id, description, location_found, date_found, image_path, image_embedding, text_embedding, qr_token, qr_code_path) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;"
            form_data = (session['user_id'], request.form['category_id'], description, request.form['location'], request.form['date'], filepath, embedding, text_emb, qr_token, qr_code_path)
        else: # lost item
            sql = "INSERT INTO lost_items (user_id, category_id, description, location_lost, date_lost, image_path, image_embedding, text_embedding) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;"
            form_data = (session['user_id'], request.form['category_id'], description, request.form['location'], request.form['date'], filepath, embedding, text_emb)

        cursor.execute(sql, form_data)
        new_item_id = cursor.fetchone()['id']
        conn.commit()

        if item_type == 'found':
            create_notification_for_match(conn, new_item_id)
        
        cursor.close()
        conn.close()
        
        if item_type == 'found':
            return render_template('report_success.html', qr_code_path=qr_code_path)
        else:
            return redirect(url_for('home'))

    cursor.close()
    conn.close()
    return render_template('report.html', item_type=item_type, categories=categories)


@app.route('/matches/<int:lost_item_id>')
def find_matches(lost_item_id):
    """Finds and displays potential matches for a given lost item."""
    if 'user_id' not in session: return redirect(url_for('login'))
    
    conn = get_db_connection()
    if not conn: return "Error: Could not connect to the database."

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM lost_items WHERE id = %s AND user_id = %s", (lost_item_id, session['user_id']))
    lost_item = cursor.fetchone()

    potential_matches = []
    if lost_item and lost_item.get('image_embedding'):
        cursor.execute("SELECT * FROM found_items WHERE status = 'Available' AND image_embedding IS NOT NULL")
        found_items = cursor.fetchall()
        for found_item in found_items:
            distance = hamming_distance(lost_item['image_embedding'], found_item['image_embedding'])
            if distance < 10:
                found_item['similarity_score'] = (64 - distance) / 64 * 100
                potential_matches.append(found_item)
    cursor.close()
    conn.close()
    potential_matches.sort(key=lambda x: x['similarity_score'], reverse=True)
    return render_template('matches.html', lost_item=lost_item, matches=potential_matches)


@app.route('/claim', methods=['POST'])
def claim_item():
    """Handles the item claim process by updating item statuses."""
    if 'user_id' not in session: return redirect(url_for('login'))
    
    lost_item_id = request.form.get('lost_item_id')
    found_item_id = request.form.get('found_item_id')

    conn = get_db_connection()
    if not conn: return "Error: Could not connect to the database."

    cursor = conn.cursor()
    try:
        # Security check: ensure the user owns the lost item report
        cursor.execute("SELECT id FROM lost_items WHERE id = %s AND user_id = %s", (lost_item_id, session['user_id']))
        if cursor.fetchone() is None:
            return "Permission denied.", 403

        cursor.execute("UPDATE lost_items SET status = 'Returned' WHERE id = %s", (lost_item_id,))
        cursor.execute("UPDATE found_items SET status = 'Claimed' WHERE id = %s", (found_item_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"An error occurred during the claim process: {e}")
        return "Failed to process claim."
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('home'))

@app.route('/notifications')
def notifications():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    conn = get_db_connection()
    if not conn: return "Error: Could not connect to the database."

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM notifications WHERE user_id = %s ORDER BY created_at DESC", (session['user_id'],))
    user_notifications = cursor.fetchall()
    
    cursor.execute("UPDATE notifications SET is_read = TRUE WHERE user_id = %s", (session['user_id'],))
    conn.commit()
    
    cursor.close()
    conn.close()
    
    return render_template('notifications.html', notifications=user_notifications)

@app.route('/claim/<token>')
def claim_via_qr(token):
    """Displays a public page for claiming an item via its QR token."""
    conn = get_db_connection()
    if not conn: return "Error connecting to database."

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM found_items WHERE qr_token = %s", (token,))
    found_item = cursor.fetchone()

    if not found_item:
        return "This claim link is invalid or has expired.", 404

    user_lost_items = []
    if 'user_id' in session:
        cursor.execute("SELECT * FROM lost_items WHERE user_id = %s AND status = 'Pending'", (session['user_id'],))
        user_lost_items = cursor.fetchall()

    cursor.close()
    conn.close()
    
    return render_template('claim_qr.html', found_item=found_item, user_lost_items=user_lost_items)

# --- AUTHENTICATION ROUTES ---
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handles user registration."""
    if request.method == 'POST':
        username = request.form['username']
        password_hash = generate_password_hash(request.form['password'])
        conn = get_db_connection()
        if not conn: return "Error: Could not connect to the database."
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password_hash))
            conn.commit()
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            return "Username already exists! Please choose another."
        except Exception as e:
            conn.rollback()
            return f"An error occurred: {e}"
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login and sets admin status in session."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        if not conn: return "Error: Could not connect to the database."
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user.get('is_admin', False) 
            cursor.close()
            conn.close()
            return redirect(url_for('home'))
        else:
            cursor.close()
            conn.close()
            return "Invalid username or password!"
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Clears the session to log the user out."""
    session.clear()
    return redirect(url_for('login'))

# --- ADMIN ROUTES ---
@app.route('/admin/dashboard')
def admin_dashboard():
    """Displays the admin dashboard with all items."""
    if not session.get('is_admin'): return redirect(url_for('home'))
    
    conn = get_db_connection()
    if not conn: return "Error: Could not connect to the database."

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT li.*, u.username FROM lost_items li JOIN users u ON li.user_id = u.id ORDER BY li.created_at DESC")
    all_lost_items = cursor.fetchall()
    cursor.execute("SELECT fi.*, u.username FROM found_items fi JOIN users u ON fi.user_id = u.id ORDER BY fi.created_at DESC")
    all_found_items = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('admin_dashboard.html', lost_items=all_lost_items, found_items=all_found_items)

@app.route('/admin/delete/<item_type>/<int:item_id>', methods=['POST'])
def delete_item(item_type, item_id):
    """Handles the deletion of an item by an admin."""
    if not session.get('is_admin'): return redirect(url_for('home'))
    if item_type not in ['lost_items', 'found_items']: return "Invalid item type", 404

    conn = get_db_connection()
    if not conn: return "Error: Could not connect to the database."

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        if item_type == 'found_items':
            cursor.execute("SELECT image_path, qr_code_path FROM found_items WHERE id = %s", (item_id,))
        else: # lost_items
            cursor.execute("SELECT image_path FROM lost_items WHERE id = %s", (item_id,))
        
        record = cursor.fetchone()
        if record:
            # Delete record from database first
            cursor.execute(f"DELETE FROM {item_type} WHERE id = %s", (item_id,))
            conn.commit()

            # Now delete files from the server
            image_path = record.get('image_path')
            if image_path and os.path.exists(image_path):
                os.remove(image_path)
            
            qr_code_path = record.get('qr_code_path')
            # --- FIX STARTS HERE ---
            # The path from the DB (e.g., 'static/qrcodes/...') is already correct.
            # No need to join it with app.static_folder.
            if qr_code_path and os.path.exists(qr_code_path):
                os.remove(qr_code_path)
            # --- FIX ENDS HERE ---
    except Exception as e:
        conn.rollback()
        print(f"Error deleting item: {e}")
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/analytics')
def analytics():
    """Displays an analytics dashboard for admins."""
    if not session.get('is_admin'):
        return redirect(url_for('home'))

    conn = get_db_connection()
    if not conn:
        return "Error: Could not connect to the database."
        
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Query 1: Get total counts of lost, found, and returned items
    cursor.execute("SELECT COUNT(*) FROM lost_items;")
    total_lost = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) FROM found_items;")
    total_found = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) FROM lost_items WHERE status = 'Returned';")
    total_returned = cursor.fetchone()['count']

    # Query 2: Get the most common lost item categories
    cursor.execute("""
        SELECT c.name, COUNT(li.id) as item_count
        FROM lost_items li
        JOIN categories c ON li.category_id = c.id
        GROUP BY c.name
        ORDER BY item_count DESC
        LIMIT 5;
    """)
    top_categories = cursor.fetchall()

    # Calculate recovery rate
    recovery_rate = (total_returned / total_lost * 100) if total_lost > 0 else 0
    
    cursor.close()
    conn.close()
    
    stats = {
        'total_lost': total_lost,
        'total_found': total_found,
        'total_returned': total_returned,
        'recovery_rate': round(recovery_rate, 2),
        'top_categories': top_categories
    }
    
    return render_template('analytics.html', stats=stats)

# --- APP INITIALIZATION ---
if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['QR_CODE_FOLDER'], exist_ok=True)
    app.run(debug=True)