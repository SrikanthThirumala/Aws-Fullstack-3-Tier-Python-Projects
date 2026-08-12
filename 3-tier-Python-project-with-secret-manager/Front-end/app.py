from flask import Flask, render_template, request, redirect, url_for
import requests

app = Flask(__name__)

# This is your private backend IP/Port or Internal ALB URL
BACKEND_API = "http://10.0.3.64:8000/items/"

@app.route('/', methods=['GET'])
def index():
    try:
        # Fetch data from your private backend internally
        response = requests.get(BACKEND_API)
        items = response.json() if response.status_code == 200 else []
    except Exception as e:
        print(f"Error fetching data: {e}")
        items = []
        
    return render_template('index.html', items=items)

@app.route('/save', methods=['POST'])
def save_item():
    item_id = request.form.get('itemId')
    
    # Construct the payload from the form inputs
    payload = {
        'name': request.form.get('name'),
        'email': request.form.get('email'),
        'country': request.form.get('country')
    }
    
    if item_id:
        # If an ID exists, we are updating an existing record (PUT)
        requests.put(f"{BACKEND_API}{item_id}", json=payload)
    else:
        # If no ID exists, we are creating a new record (POST)
        requests.post(BACKEND_API, json=payload)
        
    # Reload the page to show the updated data
    return redirect(url_for('index'))

@app.route('/delete/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    # Delete the record
    requests.delete(f"{BACKEND_API}{item_id}")
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Running on port 80 means you can access it directly without Nginx
    # (Requires sudo privileges to run on port 80)
    app.run(host='0.0.0.0', port=80)