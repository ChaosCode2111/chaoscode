import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from models import db, User, Snippet  # Import from our models.py

# --- CONFIGURATION ---

# Set the owner's username here. Only this user can access /admin
OWNER_USERNAME = "chaosadi" # <-- CHANGE THIS to your desired owner username

app = Flask(__name__)
app.config['SECRET_KEY'] = 'YOUR_SECRET_KEY' # <-- CHANGE THIS to a long random string
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- INITIALIZATION ---
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index' # Redirect to index if user tries to access a protected page
login_manager.login_message = "You need to log in to see this page, pal!"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- HELPER FUNCTION FOR ADMIN ---
def is_owner():
    return current_user.is_authenticated and current_user.username == OWNER_USERNAME

# --- CORE PAGES (Page 1, 2, 3) ---

@app.route('/')
def index():
    """Page 1: Login/Signup Page"""
    if current_user.is_authenticated:
        return redirect(url_for('categories'))
    return render_template('index.html')

@app.route('/categories')
def categories():
    """Page 2: All Categories"""
    # Get all unique categories from the database
    categories = db.session.query(Snippet.category).distinct().all()
    # categories will be a list of tuples like [('Python',), ('Java',)]
    category_names = [c[0] for c in categories]
    return render_template('categories.html', categories=category_names, is_owner=is_owner())

@app.route('/category/<string:category_name>')
def show_snippets(category_name):
    """Page 3: Code Snippets for a Category"""
    snippets = Snippet.query.filter_by(category=category_name).all()
    
    saved_snippet_ids = []
    if current_user.is_authenticated:
        saved_snippet_ids = [snippet.id for snippet in current_user.saved]
        
    return render_template('snippets.html', 
                           snippets=snippets, 
                           category_name=category_name, 
                           saved_snippet_ids=saved_snippet_ids,
                           is_owner=is_owner())

# --- USER & AUTHENTICATION ROUTES ---

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form.get('username')
    password = request.form.get('password')
    
    user = User.query.filter_by(username=username).first()
    if user:
        flash('Username already exists! Try a crazier one!', 'error')
        return redirect(url_for('index'))
        
    new_user = User(username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    
    login_user(new_user)
    return redirect(url_for('categories'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        flash('Incorrect details. Please put the correct username and password.', 'error') # <-- NEW MESSAGE
        return redirect(url_for('index'))
        
    login_user(user)
    return redirect(url_for('categories'))

@app.route('/skip')
def skip_login():
    """Skip login option"""
    return redirect(url_for('categories'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# --- USER DASHBOARD & SAVING ---

@app.route('/dashboard')
@login_required
def dashboard():
    """User Dashboard: Shows saved snippets"""
    saved_snippets = current_user.saved
    return render_template('dashboard.html', snippets=saved_snippets, is_owner=is_owner())

@app.route('/save_snippet/<int:snippet_id>', methods=['POST'])
@login_required
def save_snippet(snippet_id):
    """API-like route to save a snippet"""
    snippet = Snippet.query.get(snippet_id)
    if not snippet:
        return jsonify({'success': False, 'error': 'Snippet not found'}), 404
    
    if snippet in current_user.saved:
        # Already saved, so unsave it
        current_user.saved.remove(snippet)
        db.session.commit()
        return jsonify({'success': True, 'action': 'unsaved'})
    else:
        # Not saved, so save it
        current_user.saved.append(snippet)
        db.session.commit()
        return jsonify({'success': True, 'action': 'saved'})

# --- !!! OWNER ADMIN PAGE !!! ---

@app.route('/admin')
@login_required
def admin():
    """Admin Page: For Uploading, Deleting, Modifying"""
    if not is_owner():
        flash("Whoa there! That's a super-secret page only for the owner!", "error")
        return redirect(url_for('categories'))
        
    all_snippets = Snippet.query.all()
    return render_template('admin.html', snippets=all_snippets, is_owner=is_owner())

@app.route('/admin/add', methods=['POST'])
@login_required
def admin_add_snippet():
    if not is_owner():
        return redirect(url_for('categories'))
        
    category = request.form.get('category')
    title = request.form.get('title')
    code = request.form.get('code')
    
    new_snippet = Snippet(category=category, title=title, code=code)
    db.session.add(new_snippet)
    db.session.commit()
    
    flash('BOOM! New code snippet added!', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/delete/<int:snippet_id>', methods=['POST'])
@login_required
def admin_delete_snippet(snippet_id):
    print(f"--- ATTEMPTING DELETE for ID: {snippet_id} ---") # <--- ADD THIS
    
    if not is_owner():
        print("DELETE FAILED: User is not owner.") # <--- ADD THIS
        return jsonify({'success': False, 'message': 'Permission Denied'}), 403
        
    snippet = Snippet.query.get(snippet_id)
    if not snippet:
        print(f"DELETE FAILED: Snippet {snippet_id} not found.") # <--- ADD THIS
        return jsonify({'success': False, 'message': 'Snippet not found'}), 404
        
    # ... deletion logic ...
    
    db.session.delete(snippet)
    db.session.commit()
    
    print(f"--- SUCCESSFUL DELETE for ID: {snippet_id} ---") # <--- ADD THIS
    return jsonify({'success': True, 'snippet_id': snippet_id, 'message': 'ZAP! Snippet deleted.'})

@app.route('/admin/update/<int:snippet_id>', methods=['POST'])
@login_required
def admin_update_snippet(snippet_id):
    if not is_owner():
        return redirect(url_for('categories'))
        
    snippet = Snippet.query.get_or_404(snippet_id)
    snippet.category = request.form.get('category')
    snippet.title = request.form.get('title')
    snippet.code = request.form.get('code')
    
    db.session.commit()
    
    flash('KACHOW! Snippet updated!', 'success')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    # Create the database if it doesn't exist
    # (This check might be better as a separate build step,
    # but is fine for now)
    with app.app_context():
        if not os.path.exists('database.db'):
            db.create_all()
            print("Database created!")

    # Get the port from Render's environment variable
    # Default to 5000 for local testing
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app on 0.0.0.0 to make it visible
    # Set debug=False for production
    app.run(host='0.0.0.0', port=port, debug=False)
