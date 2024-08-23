from flask import Flask, request, render_template, redirect, url_for, send_file
from flask_mysqldb import MySQL
import qrcode
import pdfkit
import os
import MySQLdb.cursors
import pandas as pd

app = Flask(__name__)

# Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'mesh'
app.config['MYSQL_PASSWORD'] = 'Backend123'
app.config['MYSQL_DB'] = 'meeting_system'
mysql = MySQL(app)

@app.route('/')
def index():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM meetings")
    meetings = cursor.fetchall()
    cursor.close()
    return render_template('index.html', meetings=meetings)

@app.route('/meeting/<int:meeting_id>')
def meeting(meeting_id):
    return render_template('form.html', meeting_id=meeting_id)

@app.route('/submit', methods=['POST'])
def submit():
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    email = request.form['email']
    phone = request.form['phone']
    department = request.form['department']
    meeting_id = request.form['meeting_id']

    cursor = mysql.connection.cursor()
    cursor.execute(
        "INSERT INTO attendees (first_name, last_name, email, phone, department, meeting_id) VALUES (%s, %s, %s, %s, %s, %s)",
        (first_name, last_name, email, phone, department, meeting_id)
    )
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT meetings.name, attendees.first_name, attendees.last_name, attendees.email, attendees.phone, attendees.department FROM attendees JOIN meetings ON attendees.meeting_id = meetings.id")
    data = cursor.fetchall()
    cursor.close()
    return render_template('admin.html', data=data)

@app.route('/generate_qr/<int:meeting_id>')
def generate_qr(meeting_id):
    url = url_for('meeting', meeting_id=meeting_id, _external=True)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')
    img.save(f'static/meeting_{meeting_id}_qr.png')
    return send_file(f'static/meeting_{meeting_id}_qr.png', mimetype='image/png')

@app.route('/generate_excel/<int:meeting_id>')
def generate_excel(meeting_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT name FROM meetings WHERE id=%s", (meeting_id,))
    meeting = cursor.fetchone()
    cursor.execute("SELECT first_name, last_name, email, phone, department FROM attendees WHERE meeting_id=%s", (meeting_id,))
    attendees = cursor.fetchall()
    cursor.close()

    if not meeting:
        return "Meeting not found", 404

    df = pd.DataFrame(attendees)
    output = f'static/meeting_{meeting_id}_report.xlsx'
    df.to_excel(output, index=False)

    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')



if __name__ == '__main__':
    app.run(debug=True)
