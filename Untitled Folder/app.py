from flask import Flask, render_template, request, redirect, url_for,session
import mysql.connector
from flask import jsonify
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for session management

# Establish MySQL connection
mydb = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Nayantra1234@',
    port='3306',
    database='healthcare'
)


# Define route for login page
@app.route('/login', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']  # Get role from form

        # Check user credentials and role in the database
        cursor = mydb.cursor(dictionary=True)
        query = "SELECT * FROM Users WHERE username = %s AND password = %s AND role = %s"
        cursor.execute(query, (username, password, role))
        user = cursor.fetchone()
        cursor.close()

        # If user is found and login is successful
        if user:
            session['username'] = username
            session['role'] = role
            session['user_id'] = user['user_id']  # Store user_id in session
            #hidding the user_id  by using session --> by using this security is increased

            # Redirect to respective page based on role
            if role == 'doctor':
                return redirect(url_for('doctor'))
            elif role == 'pharmacist':
                return redirect(url_for('pharmacist_dashboard'))
            elif role == 'patient':
                return redirect(url_for('patient'))
            else:
                return "Unknown role"
        else:
            return "Invalid username, password, or role"

    return render_template("login.html")

#appointment doctor
@app.route('/doctor', methods=['GET', 'POST'])
def doctor():
    if 'username' in session and session['role'] == 'doctor':
        if request.method == 'POST':
            # Handle doctor signup form submission
            # Insert new doctor information into the database
            specialization = request.form['specialization']
            availability = request.form['availability']
            phone_number = request.form['phone_number']
            user_id = session['user_id']  # Assuming user_id is stored in the session

            cursor = mydb.cursor()
            query = "INSERT INTO Doctors (user_id, specialization, availability, phone_number) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (user_id, specialization, availability, phone_number))
            mydb.commit()
            cursor.close()

            return "Doctor information submitted successfully"
        else:
            # Display doctor's appointments and render doctor signup form
            username = session['username']
            cursor = mydb.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM Appointments INNER JOIN Doctors ON Appointments.doctor_id = Doctors.doctor_id INNER JOIN Users ON Doctors.user_id = Users.user_id WHERE Users.username = %s",
                (username,))
            appointments = cursor.fetchall()
            cursor.close()
            return render_template('doctor.html', appointments=appointments)
    else:
        return redirect(url_for('login'))


# Define route for signup page
@app.route('/signup', methods=['POST'])
def signup():
    # Get form data
    username = request.form['logname']
    email = request.form['logemail']
    role = request.form['role']
    password = request.form['logpass']

    # Insert data into the database
    cursor = mydb.cursor()
    query = "INSERT INTO Users (username, email, role, password) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (username, email, role, password))
    mydb.commit()
    cursor.close()

    # Redirect to login page after signup
    return redirect(url_for('login'))
#  ---Define route for patient page--
@app.route('/patient')
def patient():
    # Retrieve available doctors from the database
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Doctors")
    doctors = cursor.fetchall()
    cursor.close()

    # Retrieve available medicines with their associated pharmacies from the database


    return render_template('patient.html', doctors=doctors)

# Route to fetch appointments booked by the patient
@app.route('/get_patient_appointments', methods=['GET'])
def get_patient_appointments():
    if 'user_id' in session and session['role'] == 'patient':
        patient_id = session['user_id']
        cursor = mydb.cursor(dictionary=True)
        query = "SELECT * FROM Appointments WHERE patient_id = %s"
        cursor.execute(query, (patient_id,))
        appointments = cursor.fetchall()
        cursor.close()
        return jsonify(appointments)
    else:
        return "Unauthorized", 401

# Route to cancel an appointment
@app.route('/cancel_appointment/<int:appointment_id>', methods=['POST'])
def cancel_appointment(appointment_id):
    if 'user_id' in session and session['role'] == 'patient':
        patient_id = session['user_id']
        cursor = mydb.cursor()
        query = "UPDATE Appointments SET status = 'canceled' WHERE appointment_id = %s AND patient_id = %s"
        cursor.execute(query, (appointment_id, patient_id))
        mydb.commit()
        cursor.close()
        return "Appointment canceled successfully"
    else:
        return "Unauthorized", 401


# Route to fetch available doctors with their names and emails
@app.route('/get_available_doctors', methods=['GET'])
def get_available_doctors():
    if 'user_id' in session and session['role'] == 'patient':
        # Retrieve available doctors from the database
        cursor = mydb.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Doctors")
        doctors = cursor.fetchall()
        cursor.close()

        return jsonify(doctors)  # Return available doctors as JSON
    else:
        return "Unauthorized"



# Define the place_order function
def place_order():
    if 'user_id' in session:
        patient_id = session['user_id']
        medicine_name = request.json['medicine_name']
        quantity = request.json['quantity']

        cursor = mydb.cursor(dictionary=True)

        # Fetch the pha_id of the medicine from the Ppharmacist table
        query = "SELECT pha_id FROM Ppharmacist WHERE medicine_name = %s"
        cursor.execute(query, (medicine_name,))
        result = cursor.fetchone()

        if result:
            pha_id = result['pha_id']

            # Insert the order into the Oorders table
            query = "INSERT INTO Oorders (patient_id, medicine_name, quantity, pha_id) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (patient_id, medicine_name, quantity, pha_id))
            mydb.commit()

            order_id = cursor.lastrowid  # Get the ID of the inserted order
            cursor.close()

            return jsonify({"success": True, "order_id": order_id})
        else:
            cursor.close()
            return jsonify({"success": False, "message": "Medicine not found"})
    else:
        return jsonify({"success": False, "message": "Unauthorized"})

# book appointments
@app.route('/book_appointment', methods=['POST'])
def book_appointment():
    if 'user_id' in session and session['role'] == 'patient':
        patient_id = session['user_id']
        doctor_id = request.form['doctor_id']
        appointment_date = request.form['appointment_date']
        status = 'scheduled'  # Or any other default status

        cursor = mydb.cursor()
        query = "INSERT INTO Appointments (patient_id, doctor_id, appointment_date, status) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (patient_id, doctor_id, appointment_date, status))
        mydb.commit()
        cursor.close()

        return "Appointment booked successfully"
    else:
        return "Unauthorized"

# Route for placing medicine order

@app.route('/delete_user', methods=['POST'])
def delete_user():
    if 'username' in session:
        current_user_id = session.get('user_id')
        role = session.get('role')
        if role == 'doctor' or role == 'patient':
            cursor = mydb.cursor()
            query = "DELETE FROM Users WHERE user_id = %s"
            cursor.execute(query, (current_user_id,))
            mydb.commit()
            cursor.close()
            session.clear()  # Clear session after deleting the user
            return redirect(url_for('login'))
        else:
            return "Unauthorized: You can only delete your own account."
    else:
        return redirect(url_for('login'))

# Route for logging out
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))

#patient_info
@app.route('/submit_patient_info', methods=['POST'])
def submit_patient_info():
    if 'user_id' in session and session['role'] == 'patient':
        patient_id = session['user_id']
        name = request.form['name']
        age = request.form['age']
        blood_pressure = request.form['blood_pressure']
        weight = request.form['weight']
        height = request.form['height']

        cursor = mydb.cursor()
        query = "INSERT INTO patient_info (patient_id, name, age, blood_pressure, weight, height) VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (patient_id, name, age, blood_pressure, weight, height))
        mydb.commit()
        cursor.close()

        return "Patient information submitted successfully"
    else:
        return "Unauthorized"



# ---- MAIN ROUTE ----
@app.route('/')
def main():
    return render_template("welcome.html")


from flask import request


@app.route('/place_order', methods=['POST'])
def place_order():
    if 'user_id' in session:
        patient_id = session['user_id']
        medicine_name = request.json['medicine_name']
        quantity = request.json['quantity']

        # Insert the order into the Oorders table
        cursor = mydb.cursor()
        query = "INSERT INTO Oorders (patient_id, medicine_name, quantity, status) VALUES (%s, %s, %s, %s)"
        values = (patient_id, medicine_name, quantity, 'pending')
        cursor.execute(query, values)
        mydb.commit()
        cursor.close()

        return jsonify({"success": True, "message": "Order placed successfully"})
    else:
        return jsonify({"success": False, "message": "Unauthorized"})

# Pharmacist dashboard route
@app.route('/pharmacist_dashboard')
def pharmacist_dashboard():
    # Check if user is logged in and is a pharmacist
    if 'role' in session and session['role'] == 'pharmacist':
        return render_template('pharmacist_dashboard.html')
    else:
        return redirect(url_for('login'))



@app.route('/available_doctors')
def see_doc():
    return render_template("available_doctors.html")

# Display available medicines for patient visible
@app.route('/get_available_medicines')
def get_available_medicines():
    cursor = mydb.cursor(dictionary=True)
    query = "SELECT * FROM Ppharmacist"
    cursor.execute(query)
    available_medicines = cursor.fetchall()
    cursor.close()

    return jsonify(available_medicines)
# Update order status to "shipped"
@app.route('/update_order_status/<int:order_id>', methods=['POST'])
def update_order_status(order_id):
    # Check if user is logged in and is a pharmacist
    if 'role' in session and session['role'] == 'pharmacist':
        if request.method == 'POST':
            cursor = mydb.cursor()
            query = "UPDATE oorders SET status = 'shipped' WHERE order_id = %s"
            cursor.execute(query, (order_id,))
            mydb.commit()
            cursor.close()
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "message": "Invalid request method"})
    else:
        return jsonify({"error": "Unauthorized access"}), 401  # Return 401 Unauthorized status
# Display orders for pharmacist
@app.route('/get_orders')
def get_orders():
    # Check if user is logged in and is a pharmacist
    if 'role' in session and session['role'] == 'pharmacist':
        cursor = mydb.cursor(dictionary=True)
        query = "SELECT * FROM oorders"
        cursor.execute(query)
        orders = cursor.fetchall()
        cursor.close()

        return jsonify(orders)
    else:
        return jsonify({"error": "Unauthorized access"}), 401  # Return 401 Unauthorized status
if __name__ == "__main__":
    app.run(debug=True)
