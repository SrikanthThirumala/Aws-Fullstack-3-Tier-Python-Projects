from flask import Flask, render_template, request, redirect, url_for
import requests
import logging
import os

app = Flask(__name__)

# ---------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------
LOG_DIR = '/var/log/sri-app-logs'
if not os.path.exists(LOG_DIR):
    LOG_DIR = 'logs'
    os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, 'frontend.log'),
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)

# Updated to target the /users endpoint base
BACKEND_API = "http://10.0.3.99:8000/users"

@app.route('/', methods=['GET'])
def index():
    try:
        logger.info("Requesting user list from backend")
        response = requests.get(BACKEND_API)
        items = response.json() if response.status_code == 200 else []
    except Exception as e:
        logger.error(f"Error fetching data from backend: {e}")
        items = []
        
    return render_template('index.html', items=items)

@app.route('/save', methods=['POST'])
def save_item():
    item_id = request.form.get('itemId')
    payload = {
        'name': request.form.get('name'),
        'email': request.form.get('email'),
        'country': request.form.get('country')
    }
    
    try:
        if item_id:
            # Updating an existing record (PUT to /users/update/<id>)
            response = requests.put(f"{BACKEND_API}/update/{item_id}", json=payload)
            logger.info(f"Forwarded UPDATE request for ID {item_id} - Status: {response.status_code}")
        else:
            # Creating a new record (POST to /users/add)
            response = requests.post(f"{BACKEND_API}/add", json=payload)
            logger.info(f"Forwarded ADD request - Status: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to communicate with backend on /save: {e}")
        
    return redirect(url_for('index'))

@app.route('/delete/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    try:
        # Deleting a record (DELETE to /users/delete/<id>)
        response = requests.delete(f"{BACKEND_API}/delete/{item_id}")
        logger.info(f"Forwarded DELETE request for ID {item_id} - Status: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to communicate with backend on /delete: {e}")
        
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
