import sqlite3
from datetime import datetime, timedelta
from flask import Flask, jsonify, render_template, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "super_secret_key_for_rental_system"

# 🔒 Aapke customized login credentials yahan set hain
ADMIN_USER = "yashik"
ADMIN_PASS = "Yashik@123"

# In-built Database Setup Logic
def init_local_db():
    conn = sqlite3.connect("rental_portal.db")
    cursor = conn.cursor()
    # Vehicles Database Setup
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rent_vehicles (
            vehicle_id TEXT PRIMARY KEY,
            model_name TEXT NOT NULL,
            vehicle_type TEXT,
            rent_per_day REAL NOT NULL,
            status TEXT DEFAULT 'AVAILABLE'
        )
    """)
    # Bookings Database Setup
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rent_bookings (
            booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id TEXT,
            customer_name TEXT NOT NULL,
            days_rented INTEGER NOT NULL,
            total_bill REAL,
            booking_date TEXT,
            return_date TEXT,
            FOREIGN KEY(vehicle_id) REFERENCES rent_vehicles(vehicle_id)
        )
    """)
    
    # 5 Premium Vehicles entry check
    cursor.execute("SELECT COUNT(*) FROM rent_vehicles")
    if cursor.fetchone()[0] == 0:
        vehicles_data = [
            ('V101', 'Swift Dzire', 'CAR', 1500, 'AVAILABLE'),
            ('V102', 'Royal Enfield', 'BIKE', 800, 'AVAILABLE'),
            ('V103', 'Mahindra Thar', 'CAR', 3000, 'AVAILABLE'),
            ('V104', 'Hyundai i20', 'CAR', 1800, 'AVAILABLE'),
            ('V105', 'KTM Duke 390', 'BIKE', 1200, 'AVAILABLE')
        ]
        cursor.executemany("INSERT INTO rent_vehicles VALUES (?, ?, ?, ?, ?)", vehicles_data)
        conn.commit()
    conn.close()

@app.route("/")
def home():
    if not session.get("logged_in"):
        return redirect(url_for("login_page"))
    return render_template("index.html")

@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")

@app.route("/api/login", methods=["POST"])
def do_login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    if username == ADMIN_USER and password == ADMIN_PASS:
        session["logged_in"] = True
        return jsonify({"success": True, "message": "Login Successful!"})
    else:
        return jsonify({"success": False, "message": "Invalid Username or Password!"})

@app.route("/logout")
def do_logout():
    session.clear()
    return redirect(url_for("login_page"))

# Live API Logs Data fetch directly from Database engine
@app.route("/api/vehicles", methods=["GET"])
def get_vehicles():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
    
    conn = sqlite3.connect("rental_portal.db")
    cursor = conn.cursor()
    cursor.execute("SELECT vehicle_id, model_name, vehicle_type, rent_per_day, status FROM rent_vehicles ORDER BY vehicle_id")
    
    vehicles = []
    for row in cursor.fetchall():
        vehicles.append({
            'id': row[0],
            'model': row[1],
            'type': row[2],
            'rent': row[3],
            'status': row[4]
        })
    conn.close()
    return jsonify(vehicles)

# Booking Validation Process with Auto-discount Trigger emulation
@app.route("/api/book", methods=["POST"])
def book_vehicle():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    v_id = data.get("vehicle_id")
    c_name = data.get("customer_name")
    days = int(data.get("days"))

    conn = sqlite3.connect("rental_portal.db")
    cursor = conn.cursor()

    cursor.execute("SELECT status, rent_per_day FROM rent_vehicles WHERE vehicle_id = ?", (v_id,))
    res = cursor.fetchone()

    if not res:
        conn.close()
        return jsonify({"success": False, "message": "Vehicle not found!"})
    if res[0] == "RENTED":
        conn.close()
        return jsonify({"success": False, "message": "Sorry, Vehicle is already rented!"})

    # PL/SQL Trigger automation replicate for discount logs
    rent = res[1]
    total_bill = rent * days
    if days > 7:
        total_bill *= 0.90

    # Auto Return Date setup
    today = datetime.now()
    b_date_str = today.strftime("%d-%b-%Y")
    r_date_str = (today + timedelta(days=days)).strftime("%d-%b-%Y")

    # Insert log data record inside structural table
    cursor.execute("""
        INSERT INTO rent_bookings (vehicle_id, customer_name, days_rented, total_bill, booking_date, return_date) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (v_id, c_name, days, total_bill, b_date_str, r_date_str))

    # Update state to RENTED instantly
    cursor.execute("UPDATE rent_vehicles SET status = 'RENTED' WHERE vehicle_id = ?", (v_id,))
    
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": f"Success! Total Bill: Rs. {total_bill} | Return Date: {r_date_str} \n(Processed via PL/SQL Schema Controller Interface)"
    })

if __name__ == "__main__":
    init_local_db()
    app.run(debug=True, port=5000)
