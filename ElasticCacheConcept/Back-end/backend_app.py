from flask import Flask, request, jsonify
import pymysql
import redis
import json

app = Flask(__name__)

# ==========================================
# 1. HARDCODED CONFIGURATIONS
# ==========================================

# PRIMARY DB (Used ONLY for POST, PUT, DELETE)
DB_PRIMARY_HOST = 'sri-rds-1.c78es4eem4ln.us-west-2.rds.amazonaws.com'
DB_PRIMARY_USER = 'admin'
DB_PRIMARY_PASSWORD = 'Admin123'
DB_NAME = 'testsridb'

# READ REPLICA DB (Used ONLY for GET requests)
DB_REPLICA_HOST = 'sri-rds-replica.c78es4eem4ln.us-west-2.rds.amazonaws.com'
DB_REPLICA_USER = 'admin'
DB_REPLICA_PASSWORD = 'Admin123'

# REDIS CONFIGURATION
REDIS_HOST = 'sri-redis-cache-blsow0.serverless.usw2.cache.amazonaws.com'
REDIS_PORT = 6379
CACHE_EXPIRATION = 3600

# Initialize Redis client with SSL and Timeouts to prevent hanging
cache = redis.Redis(
    host=REDIS_HOST, 
    port=REDIS_PORT, 
    decode_responses=True, 
    socket_timeout=3,
    socket_connect_timeout=3,
    ssl=True
)

# ==========================================
# 2. DATABASE CONNECTION HELPERS
# ==========================================

def get_primary_connection():
    return pymysql.connect(
        host=DB_PRIMARY_HOST, user=DB_PRIMARY_USER, password=DB_PRIMARY_PASSWORD,
        database=DB_NAME, cursorclass=pymysql.cursors.DictCursor
    )

def get_replica_connection():
    return pymysql.connect(
        host=DB_REPLICA_HOST, user=DB_REPLICA_USER, password=DB_REPLICA_PASSWORD,
        database=DB_NAME, cursorclass=pymysql.cursors.DictCursor
    )


# ==========================================
# 3. CACHE INVALIDATION RULES
# ==========================================

def invalidate_cache(item_id=None):
    """
    Clears the main list cache. If an item_id is provided, 
    it also clears the cache for that specific item.
    """
    cache.delete('all_items')
    if item_id:
        cache.delete(f'item_{item_id}')
    return "Cache invalidated! Next GET request will fetch fresh data from the Read Replica."


# ==========================================
# 4. API ROUTES (CRUD)
# ==========================================

# --- READ ALL (GET) ---
@app.route('/items/', methods=['GET'])
def get_items():
    cached_data = cache.get('all_items')
    
    if cached_data:
        # Data found in Redis
        return jsonify({
            "source": "HIT: Serving data from Redis Cache!",
            "data": json.loads(cached_data)
        }), 200

    # Cache Miss - Fetch from DB
    connection = get_replica_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM items")
            items = cursor.fetchall()
            
            # Save the raw data to Redis
            cache.setex('all_items', CACHE_EXPIRATION, json.dumps(items))
            
            return jsonify({
                "source": "MISS: Fetching data from the RDS Read Replica...",
                "data": items
            }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()


# --- READ ONE (GET) ---
@app.route('/items/<int:item_id>', methods=['GET'])
def get_single_item(item_id):
    cache_key = f'item_{item_id}'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        # Data found in Redis
        return jsonify({
            "source": f"HIT: Serving item {item_id} from Redis Cache!",
            "data": json.loads(cached_data)
        }), 200

    # Cache Miss - Fetch from DB
    connection = get_replica_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM items WHERE id=%s", (item_id,))
            item = cursor.fetchone()
            
            if item:
                cache.setex(cache_key, CACHE_EXPIRATION, json.dumps(item))
                return jsonify({
                    "source": f"MISS: Fetching item {item_id} from RDS Read Replica...",
                    "data": item
                }), 200
            else:
                return jsonify({"error": "Item not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()


# --- CREATE (POST) ---
@app.route('/items/', methods=['POST'])
def add_item():
    data = request.json
    connection = get_primary_connection()
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO items (name, email, country) VALUES (%s, %s, %s)"
            cursor.execute(sql, (data['name'], data['email'], data['country']))
            connection.commit()
        
        # New item added, so invalidate the main list
        debug_msg = invalidate_cache()
        
        return jsonify({"message": "Item added successfully", "cache_status": debug_msg}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()


# --- UPDATE (PUT) ---
@app.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    data = request.json
    connection = get_primary_connection()
    try:
        with connection.cursor() as cursor:
            sql = "UPDATE items SET name=%s, email=%s, country=%s WHERE id=%s"
            cursor.execute(sql, (data['name'], data['email'], data['country'], item_id))
            connection.commit()
        
        # Item changed, invalidate both the main list and the specific item's cache
        debug_msg = invalidate_cache(item_id)
        
        return jsonify({"message": f"Item {item_id} updated successfully", "cache_status": debug_msg}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()


# --- DELETE (DELETE) ---
@app.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    connection = get_primary_connection()
    try:
        with connection.cursor() as cursor:
            sql = "DELETE FROM items WHERE id=%s"
            cursor.execute(sql, (item_id,))
            connection.commit()
        
        # Item deleted, invalidate both the main list and the specific item's cache
        debug_msg = invalidate_cache(item_id)
        
        return jsonify({"message": f"Item {item_id} deleted successfully", "cache_status": debug_msg}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)