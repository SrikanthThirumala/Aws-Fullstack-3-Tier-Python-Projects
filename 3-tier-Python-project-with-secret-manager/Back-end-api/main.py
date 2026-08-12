import json
import boto3
import pymysql
from botocore.exceptions import ClientError
from flask import Flask, request, jsonify

app = Flask(__name__)

# ---------------------------------------------------------
# 1. Retrieve Credentials from AWS Secrets Manager
# ---------------------------------------------------------
def get_db_credentials():
    secret_name = "rds!db-bad200e9-b73d-4c30-bc95-a1677efbb16a"
    region_name = "ap-south-1"

    # Boto3 uses the IAM Role attached to the EC2 instance
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise Exception(f"Failed to retrieve secret: {e}")

    return json.loads(response['SecretString'])

# ---------------------------------------------------------
# 2. Database Connection Helper
# ---------------------------------------------------------
def get_db_connection():
    # Retrieves the JSON secret {"username": "...", "password": "..."}
    creds = get_db_credentials()
    
    db_user = creds.get('username')
    db_password = creds.get('password')
   
    db_host = 'sri-rds-1.c3ome6gc6134.ap-south-1.rds.amazonaws.com'
    db_port = 3306
    db_name = 'testsridb'
    
    return pymysql.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name,
        port=db_port,
        cursorclass=pymysql.cursors.DictCursor
    )

# ---------------------------------------------------------
# 3. Initialize Database Table
# ---------------------------------------------------------
with app.app_context():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(50) NOT NULL,
                    email VARCHAR(255),
                    country VARCHAR(50)
                )
            """)
        conn.commit()
    except Exception as e:
        print(f"Database initialization failed: {e}")
    finally:
        if 'conn' in locals() and conn.open:
            conn.close()

# ---------------------------------------------------------
# 4. Flask Routes with Raw SQL Queries (CRUD)
# ---------------------------------------------------------

# CREATE (POST)
@app.route('/items/', methods=['POST'])
def create_item():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email', '')
    country = data.get('country', '')

    if not name:
        return jsonify({"error": "Name is required"}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO items (name, email, country) VALUES (%s, %s, %s)"
            cursor.execute(sql, (name, email, country))
            new_id = cursor.lastrowid
        conn.commit()
        return jsonify({"id": new_id, "name": name, "email": email, "country": country}), 201
    finally:
        conn.close()

# READ ALL (GET)
@app.route('/items/', methods=['GET'])
def get_items():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, email, country FROM items")
            items = cursor.fetchall()
        return jsonify(items), 200
    finally:
        conn.close()

# READ ONE (GET)
@app.route('/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT id, name, email, country FROM items WHERE id = %s"
            cursor.execute(sql, (item_id,))
            item = cursor.fetchone()
            
        if not item:
            return jsonify({"error": "Item not found"}), 404
            
        return jsonify(item), 200
    finally:
        conn.close()

# UPDATE (PUT)
@app.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    data = request.get_json()
    name = data.get('name')
    email = data.get('email', '')
    country = data.get('country', '')

    if not name:
        return jsonify({"error": "Name is required"}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "UPDATE items SET name = %s, email = %s, country = %s WHERE id = %s"
            cursor.execute(sql, (name, email, country, item_id))
            rows_affected = cursor.rowcount
            
        if rows_affected == 0:
            return jsonify({"error": "Item not found or no changes were made"}), 404
            
        conn.commit()
        return jsonify({"id": item_id, "name": name, "email": email, "country": country}), 200
    finally:
        conn.close()

# DELETE (DELETE)
@app.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "DELETE FROM items WHERE id = %s"
            cursor.execute(sql, (item_id,))
            rows_affected = cursor.rowcount
            
        if rows_affected == 0:
            return jsonify({"error": "Item not found"}), 404
            
        conn.commit()
        return jsonify({"message": "Item deleted successfully"}), 200
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)