import json
import boto3
import pymysql
import logging
import os
from botocore.exceptions import ClientError
from flask import Flask, request, jsonify

app = Flask(__name__)

# ---------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------
LOG_DIR = '/var/log/sri-app-logs'
# Fallback to local 'logs' folder if /var/log/flask-app doesn't exist or lacks permissions
if not os.path.exists(LOG_DIR):
    LOG_DIR = 'logs'
    os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, 'api.log'),
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# AWS Secrets & DB Connection
# ---------------------------------------------------------
def get_db_credentials():
    secret_name = "rds!db-146a62f0-5b44-4baa-b67c-4d5eb94ab11d"
    region_name = "us-west-2"
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except ClientError as e:
        logger.error(f"Failed to retrieve AWS secret: {e}")
        raise Exception(f"Failed to retrieve secret: {e}")

def get_db_connection():
    creds = get_db_credentials()
    return pymysql.connect(
        host='sri-rds-main.c10c4oay0c39.us-west-2.rds.amazonaws.com',
        user=creds.get('username'),
        password=creds.get('password'),
        database='testsridb',
        port=3306,
        cursorclass=pymysql.cursors.DictCursor
    )

# ---------------------------------------------------------
# Initialize Database Table
# ---------------------------------------------------------
with app.app_context():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(50) NOT NULL,
                    email VARCHAR(255),
                    country VARCHAR(50)
                )
            """)
        conn.commit()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    finally:
        if 'conn' in locals() and conn.open:
            conn.close()

# ---------------------------------------------------------
# API Routes (CRUD)
# ---------------------------------------------------------

@app.route('/users', methods=['GET'])
def get_users():
    logger.info("Fetching all users")
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, email, country FROM users")
            users = cursor.fetchall()
        return jsonify(users), 200
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        conn.close()

@app.route('/users/add', methods=['POST'])
def add_user():
    data = request.get_json()
    name, email, country = data.get('name'), data.get('email', ''), data.get('country', '')

    if not name:
        logger.warning("Attempted to add user without a name")
        return jsonify({"error": "Name is required"}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO users (name, email, country) VALUES (%s, %s, %s)", (name, email, country))
            new_id = cursor.lastrowid
        conn.commit()
        logger.info(f"Added new user: {name} (ID: {new_id})")
        return jsonify({"id": new_id, "name": name, "email": email, "country": country}), 201
    except Exception as e:
        logger.error(f"Error adding user {name}: {e}")
        return jsonify({"error": "Failed to add user"}), 500
    finally:
        conn.close()

@app.route('/users/update/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    name, email, country = data.get('name'), data.get('email', ''), data.get('country', '')

    if not name:
        return jsonify({"error": "Name is required"}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE users SET name = %s, email = %s, country = %s WHERE id = %s", 
                           (name, email, country, user_id))
            if cursor.rowcount == 0:
                logger.warning(f"Update failed: User ID {user_id} not found")
                return jsonify({"error": "User not found"}), 404
            
        conn.commit()
        logger.info(f"Updated user ID {user_id}")
        return jsonify({"id": user_id, "name": name, "email": email, "country": country}), 200
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        return jsonify({"error": "Failed to update user"}), 500
    finally:
        conn.close()

@app.route('/users/delete/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            if cursor.rowcount == 0:
                logger.warning(f"Delete failed: User ID {user_id} not found")
                return jsonify({"error": "User not found"}), 404
            
        conn.commit()
        logger.info(f"Deleted user ID {user_id}")
        return jsonify({"message": "User deleted successfully"}), 200
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        return jsonify({"error": "Failed to delete user"}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
