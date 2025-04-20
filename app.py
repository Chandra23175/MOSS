from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2 import sql
import os

app = Flask(__name__)
CORS(app)

# PostgreSQL connection setup
conn = psycopg2.connect(
    host="localhost",
    database="store_inventory",
    user="postgres",
    password="ghost2020"
)
cur = conn.cursor()
@app.route('/')
def home():
    return render_template('dashboard_ui.html')  # Adjust as per your main HTML file

@app.route('/add_product', methods=['POST'])
def add_product():
    try:
        data = request.get_json()
        print("Received Data", data)
        
        name = data['productName']
        description = data.get('description', '')
        price = float(data['price'])
        stock_quantity = int(data['quantity'])
        expiry_date = data.get('expiryDate', None)
        reorder_level = int(data.get('reorder', 0))
        category_id = data.get('CategoryID', None)
        supplier_id = data.get('SupplierID', None)

        insert_query = """
            INSERT INTO Product (Name, Description, Price, StockQuantity, ExpiryDate, ReOrderLevel, CategoryID, SupplierID)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cur.execute(insert_query, (name, description, price, stock_quantity, expiry_date, reorder_level, category_id, supplier_id))
        conn.commit()
        return jsonify({'message': 'Product added successfully'})
    except psycopg2.errors.UniqueViolation as e:
        print("Unique violation error:", e)
        conn.rollback()
        return jsonify({'error': 'A product with this ID already exists'}), 409
    except Exception as e:
        print("Error:", e)
        conn.rollback()
        return jsonify({'error': f'Failed to add product: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
