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

def handle_db_insert(table_name, data, field_mappings):
    """
    Generic function to handle database inserts
    
    Args:
        table_name (str): Name of the database table
        data (dict): The data received from the request
        field_mappings (dict): A dictionary mapping form fields to database fields with their types
    """
    try:
        # Process the data according to the field mappings
        processed_data = {}
        
        for form_field, db_info in field_mappings.items():
            db_field = db_info.get('db_field', form_field)  # Use form field name as DB field if not specified
            
            # Check if it's a required field
            if db_info.get('required', False) and (form_field not in data or data[form_field] == ''):
                return jsonify({'error': f'{form_field} is required'}), 400
            
            # Get the value, use default if not present
            value = data.get(form_field, db_info.get('default'))
            
            # Convert the value based on its type
            if value is not None:
                try:
                    if db_info['type'] == 'int':
                        value = int(value)
                    elif db_info['type'] == 'float':
                        value = float(value)
                    # Add more type conversions as needed
                except (ValueError, TypeError):
                    return jsonify({'error': f'Invalid value for {form_field}'}), 400
            
            processed_data[db_field] = value
        
        # Build the SQL query dynamically
        columns = list(processed_data.keys())
        placeholders = ["%s"] * len(columns)
        
        query = f"""
            INSERT INTO {table_name} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
        """
        
        values = [processed_data[col] for col in columns]
        cur.execute(query, values)
        conn.commit()
        
        return jsonify({'message': f'{table_name} added successfully'})
    
    except psycopg2.errors.UniqueViolation as e:
        print(f"Unique violation error in {table_name}:", e)
        conn.rollback()
        return jsonify({'error': f'A record with this ID already exists in {table_name}'}), 409
    except Exception as e:
        print(f"Error adding to {table_name}:", e)
        conn.rollback()
        return jsonify({'error': f'Failed to add to {table_name}: {str(e)}'}), 500

@app.route('/')
def home():
    return render_template('dashboard_ui.html')  # Adjust as per your main HTML file

@app.route('/add_product', methods=['POST'])
def add_product():
    data = request.get_json()
    print("Received Product Data", data)
    
    # Define how form fields map to database fields with their types
    field_mappings = {
        'productName': {'db_field': 'Name', 'type': 'str', 'required': True},
        'description': {'db_field': 'Description', 'type': 'str', 'default': ''},
        'price': {'db_field': 'Price', 'type': 'float', 'required': True},
        'quantity': {'db_field': 'StockQuantity', 'type': 'int', 'required': True},
        'expiryDate': {'db_field': 'ExpiryDate', 'type': 'str', 'default': None},
        'reorder': {'db_field': 'ReOrderLevel', 'type': 'int', 'default': 0},
        'CategoryID': {'db_field': 'CategoryID', 'type': 'int', 'default': None},
        'SupplierID': {'db_field': 'SupplierID', 'type': 'int', 'default': None}
    }
    
    return handle_db_insert('Product', data, field_mappings)

# Example of another form handler
@app.route('/add_vendor', methods=['POST'])
def add_vendor():
    data = request.get_json()
    print("Received Vendor Data", data)
    
    # Define how form fields map to database fields
    field_mappings = {
        'vendorName': {'db_field': 'Name', 'type': 'str', 'required': True},
        'vendorEmail': {'db_field': 'Email', 'type': 'str', 'default': ''},
        'vendorNumber': {'db_field': 'contactnumber', 'type': 'int', 'default': ''},
        'vendorAddress': {'db_field': 'Address', 'type': 'str', 'default': ''}
    }
    
    return handle_db_insert('Vendor', data, field_mappings)

# Example of a category form handler
@app.route('/add_category', methods=['POST'])
def add_category():
    data = request.get_json()
    print("Received Category Data", data)
    
    field_mappings = {
        'categoryName': {'db_field': 'Name', 'type': 'str', 'required': True},
        'description': {'db_field': 'Description', 'type': 'str', 'default': ''}
    }
    
    return handle_db_insert('Category', data, field_mappings)

# Generic DB fetch function
def handle_db_fetch(table_name, columns):
    try:
        cur.execute(sql.SQL("SELECT {} FROM {}").format(
            sql.SQL(', ').join(map(sql.Identifier, columns)),
            sql.Identifier(table_name)
        ))
        rows = cur.fetchall()
        results = [dict(zip(columns, row)) for row in rows]
        return results
    except Exception as e:
        print("❌ DB fetch error:", e)
        return []

# Example: Get all products
@app.route('/get_products', methods=['GET'])
def get_products():
    columns = ["productid", "name", "description", "price", "stockquantity", "expirydate", "reorderlevel", "categoryid", "supplierid"]
    products = handle_db_fetch("product", columns)
    return jsonify(products)

@app.route('/get_instock_products')
def get_instock_products():
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM Product WHERE StockQuantity > 0")
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_products_by_category')
def get_products_by_category():
    try:
        cur = conn.cursor()
        query = """
            SELECT * FROM product ORDER BY categoryid
        """
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/get_all_sales')
def get_all_sales():
    try:
        cur = conn.cursor()
        query = """
            SELECT * FROM salesinvoice ORDER BY customerid
        """
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500    
    
@app.route('/get_all_sales_today')
def get_all_sales_today():
    try:
        cur = conn.cursor()
        query = """
            SELECT * FROM salesinvoice WHERE invoicedate = '2025-04-16'
        """
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500     


@app.route('/product_highest_sales_week')
def product_highest_sales_week():
    try:
        cur = conn.cursor()
        query = """
            SELECT product.productid, product.name, sum(linetotal) FROM product 
            JOIN salesdetail ON salesdetail.productid = product.productid 
            GROUP BY product.productid 
            ORDER BY sum(linetotal) DESC;
        """
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500  
    
@app.route('/product_highest_sales_5')
def product_highest_sales_5():
    try:
        cur = conn.cursor()
        query = """
            SELECT product.productid as id, product.name, product.categoryid as category, supplierid as sid, sum(quantity) FROM product 
            JOIN salesdetail ON product.productid = salesdetail.productid 
            GROUP BY product.productid 
            ORDER BY sum(quantity) DESC 
            LIMIT 5;
        """
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500    

@app.route('/sales_return')
def sales_return():
    try:
        cur = conn.cursor()
        query = """
            SELECT * FROM returns ORDER BY returnid
        """
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500    

@app.route('/list_employees')
def list_employees():
    try:
        cur = conn.cursor()
        query = """
            SELECT * FROM employee ORDER BY employeeid
        """
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500  

@app.route('/best_employees')
def best_employees():
    try:
        cur = conn.cursor()
        query = """
            select employee.employeeid, employee.name, count(invoiceid) as sales_made, sum(totalamount) from salesinvoice
            join employee on employee.employeeid = salesinvoice.employeeid 
            group by employee.employeeid 
            order by sum(totalamount) desc;
        """
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500 
    
@app.route('/best_employee_today')
def best_employee_today():
    try:
        cur = conn.cursor()
        query = """
            select employeeid, count(invoiceid) from salesinvoice 
            where invoicedate = '2024-10-31' 
            group by employeeid order by count(invoiceid) desc;
            """
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500     


@app.route('/list_customers')
def list_customers():
    try:
        cur = conn.cursor()
        query = """
            select * from customer order by customerid
            """
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500     
    
@app.route('/list_customers_expenditure')
def list_customers_expenditure():
    try:
        cur = conn.cursor()
        query = """
            select customer.customerid, customer.name, count(invoiceid) as totalpurchases, sum(totalamount) as totalspent from customer 
            join salesinvoice on customer.customerid = salesinvoice.customerid  
            group by customer.customerid 
            order by sum(totalamount) desc;
            """
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500      

@app.route('/list_customers_expenditure_6')
def list_customers_expenditure_6():
    try:
        cur = conn.cursor()
        query = """
        select customer.customerid, customer.name, count(invoiceid) as totalpurchases, sum(totalamount) as totalspent from customer 
        join salesinvoice on customer.customerid = salesinvoice.customerid 
        where invoicedate between '2024-09-01' and '2025-02-28' 
        group by customer.customerid 
        order by sum(totalamount) desc limit 5;
            """
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500  
    
@app.route('/inventory_spend_month')
def inventory_spend_month():
    try:
        cur = conn.cursor()
        query = """
            select sum(totalamount) from purchaseorder 
            where orderdate between '2025-01-01' and '2025-01-31';
            """
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500  

@app.route('/revenue_last_month')
def revenue_last_month():
    try:
        cur = conn.cursor()
        query = """
            select sum(totalamount) as totalrevenue from salesinvoice 
            where invoicedate between '2024-05-01' and '2024-05-31';
            """
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500     
    
@app.route('/highest_purchase')
def highest_purchase():
    try:
        cur = conn.cursor()
        query = """
            select * from purchaseorder 
            order by totalamount desc;
            """
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500      

@app.route('/transactionlog')
def transactionlog():
    try:
        cur = conn.cursor()
        query = """
            select * from transactionlog 
            order by logid;
            """
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500         

@app.route('/feedback')
def feedback():
    try:
        cur = conn.cursor()
        query = """
            select * from feedback 
            order by feedbackid;
            """
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500 
    
@app.route('/complaints')
def complaints():
    try:
        cur = conn.cursor()
        query = """
            select * from complaints 
            order by complaintid;
            """
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500 
    
@app.route('/list_vendors')
def list_vendors():
    try:
        cur = conn.cursor()
        query = """
            select * from supplier
            order by supplierid;
            """
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500    

@app.route('/list_unique_vendors')
def list_unique_vendors():
    try:
        cur = conn.cursor()
        query = """
            SELECT s.SupplierID, s.Name, 
            COUNT(DISTINCT p.ProductID) AS UniqueProductsSold
            FROM Supplier s
            JOIN Product p ON s.SupplierID = p.SupplierID
            WHERE p.ProductID IN (
                SELECT DISTINCT p.productid
                FROM SalesInvoice si
                WHERE si.InvoiceDate >= CURRENT_DATE - INTERVAL '1 year'
            )
            GROUP BY s.SupplierID, s.Name
            ORDER BY UniqueProductsSold DESC
            LIMIT 3;
            """
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500       
        
if __name__ == '__main__':
    app.run(debug=True)


