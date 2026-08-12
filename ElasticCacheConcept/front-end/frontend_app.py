from flask import Flask, render_template, request, redirect, url_for
import requests

app = Flask(__name__)

# ==========================================
# BACKEND API ROUTING
# ==========================================
# Make sure this matches your actual backend IP or internal ALB DNS
BACKEND_URL = "http://10.0.3.39:8000/items/"


# --- HOME PAGE (READ ALL) ---
@app.route('/')
def index():
    try:
        response = requests.get(BACKEND_URL)
        response_json = response.json()
        
        items = response_json.get("data", [])
        cache_source = response_json.get("source", "No cache status available")
        
    except Exception as e:
        items = []
        cache_source = f"Error connecting to backend API: {str(e)}"

    return render_template('index.html', items=items, cache_source=cache_source)


# --- VIEW SINGLE ITEM (READ ONE) ---
@app.route('/item/<int:item_id>')
def view_item(item_id):
    try:
        response = requests.get(f"{BACKEND_URL}{item_id}")
        response_json = response.json()
        
        item = response_json.get("data", None)
        cache_source = response_json.get("source", "No cache status available")
        
    except Exception as e:
        item = None
        cache_source = f"Error connecting to backend API: {str(e)}"

    return render_template('detail.html', item=item, cache_source=cache_source)


# --- ADD ITEM (CREATE) ---
@app.route('/add', methods=['POST'])
def add_item():
    data = {
        "name": request.form.get("name"),
        "email": request.form.get("email"),
        "country": request.form.get("country")
    }
    
    requests.post(BACKEND_URL, json=data)
    return redirect(url_for('index'))


# --- EDIT ITEM (UPDATE) ---
@app.route('/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    if request.method == 'POST':
        # Grab updated data from the form
        data = {
            "name": request.form.get("name"),
            "email": request.form.get("email"),
            "country": request.form.get("country")
        }
        
        # Send a PUT request to the backend to update the Primary DB
        requests.put(f"{BACKEND_URL}{item_id}", json=data)
        
        # Redirect back to the home page
        return redirect(url_for('index'))
        
    else:
        # GET Request: Fetch current item data to pre-fill the edit form
        try:
            response = requests.get(f"{BACKEND_URL}{item_id}")
            item = response.json().get("data", None)
        except Exception:
            item = None
            
        return render_template('edit.html', item=item)


# --- DELETE ITEM (DELETE) ---
@app.route('/delete/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    requests.delete(f"{BACKEND_URL}{item_id}")
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)