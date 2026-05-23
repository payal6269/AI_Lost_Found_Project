import base64
import csv
import io
import psycopg2
import psycopg2.extras
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
from datetime import datetime
from ai_matcher import find_matches, accuracy_summary
from database import get_db_connection, init_db

app = Flask(__name__)
app.secret_key = 'lostnfound-secret-2024'

ADMIN_SECRET = 'admin@704'
CATEGORIES = ['Electronics', 'Clothing', 'Documents', 'Accessories', 'Keys', 'Bags', 'Other']

init_db()

def is_admin():
    return session.get('role') == 'admin'

def qry(conn, sql, params=(), one=False):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(sql, params)
    return (cur.fetchone() if one else cur.fetchall()), cur

def run(conn, sql, params=()):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(sql, params)
    conn.commit()
    return cur

# ─── AUTH ────────────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name    = request.form.get('name', '').strip()
        roll_no = request.form.get('roll_no', '').strip()
        reg_type = request.form.get('reg_type')
        if not name or not roll_no:
            flash('Please fill all fields.', 'error')
            return redirect(url_for('register'))
        role = 'admin' if reg_type == 'admin' else 'user'
        if reg_type == 'admin' and roll_no != ADMIN_SECRET:
            flash('Invalid admin secret key!', 'error')
            return redirect(url_for('register'))
        conn = get_db_connection()
        rows, _ = qry(conn, 'SELECT id FROM users WHERE roll_no=%s', (roll_no,))
        if rows:
            flash('This Roll No is already registered!', 'error')
            conn.close(); return redirect(url_for('register'))
        run(conn, 'INSERT INTO users (name, roll_no, role) VALUES (%s,%s,%s)', (name, roll_no, role))
        conn.close()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name    = request.form.get('name', '').strip()
        roll_no = request.form.get('roll_no', '').strip()
        conn = get_db_connection()
        rows, _ = qry(conn, 'SELECT * FROM users WHERE name=%s AND roll_no=%s', (name, roll_no))
        conn.close()
        if rows:
            user = rows[0]
            session['user_name'] = user['name']
            session['role']      = user['role']
            session['user_id']   = user['id']
            flash(f"Welcome back, {user['name']}!", 'success')
            return redirect(url_for('index'))
        flash('Invalid name or password.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

# ─── MAIN ────────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_name' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    rows, _ = qry(conn, "SELECT COUNT(*) as c FROM items WHERE type='lost' AND status='active'")
    total_lost = rows[0]['c']
    rows, _ = qry(conn, "SELECT COUNT(*) as c FROM items WHERE type='found' AND status='active'")
    total_found = rows[0]['c']
    rows, _ = qry(conn, "SELECT COUNT(*) as c FROM items WHERE status='claimed'")
    total_claimed = rows[0]['c']
    recent_items, _ = qry(conn, "SELECT * FROM items WHERE status='active' ORDER BY id DESC LIMIT 4")
    lost_rows, _    = qry(conn, "SELECT name FROM items WHERE type='lost' AND status='active'")
    conn.close()
    lost_names = [r['name'] for r in lost_rows]
    return render_template('index.html', user_name=session['user_name'],
                           is_admin=is_admin(), total_lost=total_lost,
                           total_found=total_found, total_claimed=total_claimed,
                           recent_items=recent_items, lost_names=lost_names)

# ─── REPORT ──────────────────────────────────────────────

def handle_image(file):
    if file and file.filename:
        image_bytes = file.read()
        if image_bytes:
            mime = file.content_type or 'image/jpeg'
            return mime + '|' + base64.b64encode(image_bytes).decode('utf-8')
    return ''

@app.route('/report_lost', methods=['GET', 'POST'])
def report_lost():
    if 'user_name' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        image_data = handle_image(request.files.get('image'))
        conn = get_db_connection()
        cur = run(conn, '''INSERT INTO items
            (name,description,category,type,image_data,reported_by,phone,email,reported_at,status,location)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id''',
            (request.form.get('name'), request.form.get('description'),
             request.form.get('category','Other'), 'lost', image_data,
             session['user_name'], request.form.get('phone',''),
             request.form.get('email',''), datetime.now().strftime('%Y-%m-%d %H:%M'),
             'active', request.form.get('location','')))
        new_id = cur.fetchone()['id']
        conn.close()
        flash('Lost item reported! Here are AI-suggested matches.', 'success')
        return redirect(url_for('ai_match', item_id=new_id))
    return render_template('report_lost.html', categories=CATEGORIES)

@app.route('/report_found', methods=['GET', 'POST'])
def report_found():
    if 'user_name' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        image_data = handle_image(request.files.get('image'))
        conn = get_db_connection()
        run(conn, '''INSERT INTO items
            (name,description,category,type,image_data,reported_by,phone,email,reported_at,status,location)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
            (request.form.get('name'), request.form.get('description'),
             request.form.get('category','Other'), 'found', image_data,
             session['user_name'], request.form.get('phone',''),
             request.form.get('email',''), datetime.now().strftime('%Y-%m-%d %H:%M'),
             'active', request.form.get('location','')))
        conn.close()
        flash('Found item reported successfully!', 'success')
        return redirect(url_for('view_items'))
    return render_template('report_found.html', categories=CATEGORIES)

# ─── VIEW ────────────────────────────────────────────────

@app.route('/view_items')
def view_items():
    if 'user_name' not in session: return redirect(url_for('login'))
    sort         = request.args.get('sort', 'newest')
    filter_status = request.args.get('status', 'all')
    filter_type  = request.args.get('type', 'all')
    filter_cat   = request.args.get('category', 'all')
    q = request.args.get('q', '').strip()

    params = []
    query  = 'SELECT * FROM items WHERE 1=1'
    if filter_status != 'all': query += ' AND status=%s';    params.append(filter_status)
    if filter_type   != 'all': query += ' AND type=%s';      params.append(filter_type)
    if filter_cat    != 'all': query += ' AND category=%s';  params.append(filter_cat)
    if q:
        query += ' AND (name ILIKE %s OR description ILIKE %s)'; params += [f'%{q}%', f'%{q}%']
    query += ' ORDER BY id ' + ('ASC' if sort == 'oldest' else 'DESC')

    conn = get_db_connection()
    items, _ = qry(conn, query, params)
    conn.close()
    return render_template('view_items.html', items=items, is_admin=is_admin(),
                           sort=sort, filter_status=filter_status,
                           filter_type=filter_type, filter_cat=filter_cat,
                           categories=CATEGORIES, q=q)

# ─── MY ITEMS ────────────────────────────────────────────

@app.route('/my_items')
def my_items():
    if 'user_name' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    items, _ = qry(conn, "SELECT * FROM items WHERE reported_by=%s ORDER BY id DESC", (session['user_name'],))
    conn.close()
    return render_template('my_items.html', items=items, is_admin=is_admin())

# ─── ITEM DETAIL ─────────────────────────────────────────

@app.route('/item/<int:item_id>')
def item_detail(item_id):
    if 'user_name' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    rows, _ = qry(conn, 'SELECT * FROM items WHERE id=%s', (item_id,))
    conn.close()
    if not rows:
        flash('Item not found.', 'error'); return redirect(url_for('view_items'))
    return render_template('item_detail.html', item=rows[0], is_admin=is_admin())

# ─── CLAIM ───────────────────────────────────────────────

@app.route('/claim_request/<int:item_id>', methods=['GET', 'POST'])
def claim_request(item_id):
    if 'user_name' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    rows, _ = qry(conn, 'SELECT * FROM items WHERE id=%s', (item_id,))
    item = rows[0] if rows else None
    if request.method == 'POST':
        run(conn, '''INSERT INTO claim_requests
            (item_id,item_name,requested_by,user_phone,user_email,message,requested_at,status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)''',
            (item_id, item['name'], session['user_name'],
             request.form.get('phone',''), request.form.get('email',''),
             request.form.get('message',''), datetime.now().strftime('%Y-%m-%d %H:%M'), 'pending'))
        conn.close()
        flash('Claim request sent!', 'success')
        return redirect(url_for('view_items'))
    conn.close()
    return render_template('claim_request.html', item=item)

@app.route('/approve_claim/<int:claim_id>')
def approve_claim(claim_id):
    if not is_admin(): return redirect(url_for('view_items'))
    conn = get_db_connection()
    rows, _ = qry(conn, 'SELECT * FROM claim_requests WHERE id=%s', (claim_id,))
    claim = rows[0]
    run(conn, "UPDATE claim_requests SET status='approved' WHERE id=%s", (claim_id,))
    run(conn, "UPDATE items SET status='claimed' WHERE id=%s", (claim['item_id'],))
    conn.close()
    flash('Claim approved!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/reject_claim/<int:claim_id>')
def reject_claim(claim_id):
    if not is_admin(): return redirect(url_for('view_items'))
    conn = get_db_connection()
    run(conn, "UPDATE claim_requests SET status='rejected' WHERE id=%s", (claim_id,))
    conn.close()
    flash('Claim rejected.', 'error')
    return redirect(url_for('admin_panel'))

# ─── ADMIN ───────────────────────────────────────────────

@app.route('/admin')
def admin_panel():
    if not is_admin(): return redirect(url_for('index'))
    conn = get_db_connection()
    items,  _ = qry(conn, 'SELECT * FROM items ORDER BY id DESC')
    users,  _ = qry(conn, 'SELECT * FROM users ORDER BY id DESC')
    claims, _ = qry(conn, 'SELECT * FROM claim_requests ORDER BY id DESC')
    stats,  _ = qry(conn, """
        SELECT category,
               SUM(CASE WHEN type='lost'  THEN 1 ELSE 0 END) as lost_count,
               SUM(CASE WHEN type='found' THEN 1 ELSE 0 END) as found_count
        FROM items GROUP BY category ORDER BY category
    """)
    conn.close()
    return render_template('admin.html', items=items, users=users,
                           claims=claims, category_stats=stats)

@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if not is_admin(): return redirect(url_for('index'))
    if user_id == session.get('user_id'):
        flash('Cannot delete your own account.', 'error')
        return redirect(url_for('admin_panel'))
    conn = get_db_connection()
    run(conn, 'DELETE FROM users WHERE id=%s', (user_id,))
    conn.close()
    flash('User deleted.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/export_csv')
def export_csv():
    if not is_admin(): return redirect(url_for('index'))
    conn = get_db_connection()
    items, _ = qry(conn, 'SELECT id,name,description,category,type,reported_by,phone,email,reported_at,status,location FROM items ORDER BY id DESC')
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID','Name','Description','Category','Type','Reported By','Phone','Email','Reported At','Status','Location'])
    for item in items:
        writer.writerow([item.get(k,'') for k in ['id','name','description','category','type','reported_by','phone','email','reported_at','status','location']])
    output.seek(0)
    return Response(output.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=lost_found_items.csv'})

@app.route('/delete_item/<int:item_id>')
def delete_item(item_id):
    if not is_admin():
        flash('Only admin can delete items.', 'error')
        return redirect(url_for('view_items'))
    conn = get_db_connection()
    run(conn, 'DELETE FROM items WHERE id=%s', (item_id,))
    conn.close()
    flash('Item deleted.', 'success')
    return redirect(url_for('view_items'))

@app.route('/edit_item/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    if not is_admin(): return redirect(url_for('view_items'))
    conn = get_db_connection()
    if request.method == 'POST':
        run(conn, 'UPDATE items SET name=%s,description=%s,category=%s,type=%s,phone=%s,email=%s,location=%s WHERE id=%s',
            (request.form.get('name'), request.form.get('description'),
             request.form.get('category','Other'), request.form.get('type'),
             request.form.get('phone',''), request.form.get('email',''),
             request.form.get('location',''), item_id))
        conn.close()
        flash('Item updated.', 'success')
        return redirect(url_for('view_items'))
    rows, _ = qry(conn, 'SELECT * FROM items WHERE id=%s', (item_id,))
    conn.close()
    return render_template('edit_item.html', item=rows[0], categories=CATEGORIES)

@app.route('/mark_claimed/<int:item_id>')
def mark_claimed(item_id):
    if not is_admin(): return redirect(url_for('view_items'))
    conn = get_db_connection()
    run(conn, "UPDATE items SET status='claimed' WHERE id=%s", (item_id,))
    conn.close()
    flash('Item marked as claimed.', 'success')
    return redirect(url_for('view_items'))

@app.route('/reactivate_item/<int:item_id>')
def reactivate_item(item_id):
    if not is_admin(): return redirect(url_for('view_items'))
    conn = get_db_connection()
    run(conn, "UPDATE items SET status='active' WHERE id=%s", (item_id,))
    conn.close()
    flash('Item reactivated.', 'success')
    return redirect(url_for('view_items'))

# ─── MESSAGING ───────────────────────────────────────────

@app.route('/messages/<int:item_id>', methods=['GET', 'POST'])
def messages(item_id):
    if 'user_name' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    rows, _ = qry(conn, 'SELECT * FROM items WHERE id=%s', (item_id,))
    if not rows:
        conn.close(); flash('Item not found.', 'error'); return redirect(url_for('view_items'))
    item = rows[0]
    current_user = session['user_name']
    item_owner   = item['reported_by']
    if current_user == item_owner:
        lm, _ = qry(conn, 'SELECT sender FROM messages WHERE item_id=%s AND sender!=%s ORDER BY id DESC LIMIT 1', (item_id, current_user))
        other_user = lm[0]['sender'] if lm else None
    else:
        other_user = item_owner
    if request.method == 'POST':
        msg_text = request.form.get('message','').strip()
        receiver = request.form.get('receiver','').strip()
        if msg_text and receiver:
            run(conn, 'INSERT INTO messages (item_id,sender,receiver,message,sent_at) VALUES (%s,%s,%s,%s,%s)',
                (item_id, current_user, receiver, msg_text, datetime.now().strftime('%Y-%m-%d %H:%M')))
            if current_user == item_owner: other_user = receiver
    run(conn, "UPDATE messages SET is_read=1 WHERE item_id=%s AND receiver=%s", (item_id, current_user))
    thread, _ = qry(conn, 'SELECT * FROM messages WHERE item_id=%s ORDER BY id ASC', (item_id,))
    conn.close()
    return render_template('messages.html', item=item, thread=thread,
                           current_user=current_user, other_user=other_user)

@app.route('/inbox')
def inbox():
    if 'user_name' not in session: return redirect(url_for('login'))
    current_user = session['user_name']
    conn = get_db_connection()
    threads, _ = qry(conn, '''
        SELECT m.item_id, i.name as item_name,
               MAX(m.sent_at) as last_msg,
               SUM(CASE WHEN m.is_read=0 AND m.receiver=%s THEN 1 ELSE 0 END) as unread
        FROM messages m JOIN items i ON i.id=m.item_id
        WHERE m.sender=%s OR m.receiver=%s
        GROUP BY m.item_id, i.name ORDER BY last_msg DESC
    ''', (current_user, current_user, current_user))
    conn.close()
    return render_template('inbox.html', threads=threads, current_user=current_user)

@app.route('/unread_count')
def unread_count():
    if 'user_name' not in session: return {'count': 0}
    conn = get_db_connection()
    rows, _ = qry(conn, "SELECT COUNT(*) as c FROM messages WHERE receiver=%s AND is_read=0", (session['user_name'],))
    conn.close()
    return {'count': rows[0]['c']}

# ─── AI MATCHING ─────────────────────────────────────────

@app.route('/ai_match/<int:item_id>')
def ai_match(item_id):
    if 'user_name' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    rows, _ = qry(conn, 'SELECT * FROM items WHERE id=%s', (item_id,))
    if not rows or rows[0]['type'] != 'lost':
        conn.close(); flash('AI matching only works for lost items.', 'error')
        return redirect(url_for('view_items'))
    lost_item = rows[0]
    found_items, _ = qry(conn, "SELECT * FROM items WHERE type='found' AND status='active'")
    conn.close()
    matches = find_matches(dict(lost_item), [dict(f) for f in found_items], top_n=5)
    label, top_score = accuracy_summary(matches)
    return render_template('ai_match.html', lost_item=lost_item,
                           matches=matches, label=label, top_score=top_score)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
