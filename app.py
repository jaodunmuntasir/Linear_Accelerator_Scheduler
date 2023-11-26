from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, redirect, url_for, render_template, flash
from flask_migrate import Migrate
from sqlalchemy import func, extract
from flask import jsonify
import datetime
import random
import os
os.urandom(16)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    organ_type = db.Column(db.String(50), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    number_of_fractions = db.Column(db.Integer, nullable=False)
    patient_type = db.Column(db.String(20), nullable=False)  # 'indoor' or 'outdoor'
    treatment_duration = db.Column(db.Integer, nullable=False)  # Duration in minutes

class LinearAccelerator(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50))  # e.g., TrueBeam, VitalBeam, etc.
    characteristics = db.Column(db.Text)  # Additional details about the machine
    appointments = db.relationship('Appointment', backref='linear_accelerator', lazy=True)
    is_active = db.Column(db.Boolean, default=True)  # Machine on/off state
    operation_start_time = db.Column(db.Time)  # Operation start time
    operation_end_time = db.Column(db.Time)  # Operation end time
    pause_start_time = db.Column(db.DateTime)  # Pause start time
    pause_end_time = db.Column(db.DateTime)  # Pause end time

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    linear_accelerator_id = db.Column(db.Integer, db.ForeignKey('linear_accelerator.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    notes = db.Column(db.Text)

    # Relationships
    patient = db.relationship('Patient', backref=db.backref('appointments', lazy=True))
    #linear_accelerator = db.relationship('LinearAccelerator', backref=db.backref('appointments', lazy=True))

# Define a simple mapping of machine names to IDs
machine_id_map = {
    'TB1': 1, 'TB2': 2, 'VB1': 3, 'VB2': 4, 'U': 5
}

organ_to_machine_map = {
    'Craniospinal': ['TB1', 'TB2'],
    'Breast': ['TB1', 'TB2', 'VB1', 'VB2', 'U'],
    'Breast special': ['TB1', 'TB2'],
    'Head & neck': ['TB1', 'TB2', 'VB1', 'VB2'],
    'Abdomen': ['TB1', 'TB2', 'VB1', 'VB2'],
    'Pelvis': ['TB1', 'TB2', 'VB1', 'VB2'],
    'Crane': ['TB1', 'TB2', 'VB1', 'VB2'],
    'Lung': ['TB1', 'TB2', 'VB1', 'VB2'],
    'Lung special': ['TB1', 'TB2', 'VB1', 'VB2'],
    'Whole Brain': ['VB1', 'VB2', 'U']
}

def get_machine_id(machine_name):
    return machine_id_map[machine_name]

def get_next_session_date(current_date):
    next_date = current_date

    # Assuming sessions are on weekdays, increment the date skipping weekends
    next_date += datetime.timedelta(days=1)

    while next_date.weekday() >= 5:  # 5 and 6 correspond to Saturday and Sunday
        next_date += datetime.timedelta(days=1)

    return next_date

def populate_linear_accelerators():
    machines = [
        {'id': 1, 'name': 'TB1', 'type': 'Type1', 'characteristics': 'Characteristics for TB1'},
        {'id': 2, 'name': 'TB2', 'type': 'Type2', 'characteristics': 'Characteristics for TB2'},
        {'id': 3, 'name': 'VB1', 'type': 'Type3', 'characteristics': 'Characteristics for VB1'},
        {'id': 4, 'name': 'VB2', 'type': 'Type4', 'characteristics': 'Characteristics for VB2'},
        {'id': 5, 'name': 'U', 'type': 'Type5', 'characteristics': 'Characteristics for U'},
    ]

    for machine in machines:
        existing_machine = LinearAccelerator.query.get(machine['id'])
        if not existing_machine:
            new_machine = LinearAccelerator(id=machine['id'], name=machine['name'],
                                            type=machine['type'], characteristics=machine['characteristics'])
            db.session.add(new_machine)

    db.session.commit()

def find_suitable_appointment_time(machine):
    # Define the time range for appointments (e.g., 8 AM to 6 PM)
    start_hour = 8
    end_hour = 22
    current_date = datetime.datetime.now().date()
    start_datetime = datetime.datetime.combine(current_date, datetime.time(start_hour, 0))

    while start_datetime.time() < datetime.time(end_hour, 0):
        # Check if the time is within machine's operating hours and not in pause time
        if (not machine.operation_start_time or machine.operation_start_time <= start_datetime.time()) and \
           (not machine.operation_end_time or machine.operation_end_time >= start_datetime.time()) and \
           (not machine.pause_start_time or machine.pause_start_time > start_datetime) and \
           (not machine.pause_end_time or machine.pause_end_time < start_datetime):

            # Check if the time slot is not already taken by another appointment
            existing_appointment = Appointment.query.filter_by(
                linear_accelerator_id=machine.id,
                date=start_datetime
            ).first()
            if not existing_appointment:
                return start_datetime  # Suitable time found

        # Increment the time for the next check (e.g., in 30-minute intervals)
        start_datetime += datetime.timedelta(minutes=5)

    return None  # No suitable time found

def get_machine_usage_stats(machine_id, start_date, end_date):
    # Query to count the number of appointments and sum treatment durations
    stats = db.session.query(
        func.count(Appointment.id).label('patient_count'),
        func.sum(Patient.treatment_duration).label('total_hours')
    ).join(Patient, Appointment.patient_id == Patient.id)\
     .filter(
        Appointment.linear_accelerator_id == machine_id,
        Appointment.date >= start_date,
        Appointment.date <= end_date
    ).group_by(Appointment.linear_accelerator_id).first()

    return {
        'patient_count': stats.patient_count if stats else 0,
        'total_hours': stats.total_hours if stats else 0
    }

def count_appointments_by_machine(date):
    counts = db.session.query(
        Appointment.linear_accelerator_id,
        func.count(Appointment.id)
    ).filter(
        func.date(Appointment.date) == date
    ).group_by(
        Appointment.linear_accelerator_id
    ).all()

    return {machine_id: count for machine_id, count in counts}

@app.cli.command('populate-linacs')
def populate_linacs():
    populate_linear_accelerators()
    print("Linear accelerators populated in the database.")

# Filter to format datetime objects
@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%dT%H:%M'):
    if value is None:
        return ""
    return value.strftime(format)

# Filter to format time objects
@app.template_filter('timeformat')
def timeformat(value, format='%H:%M'):
    if value is None:
        return ""
    return value.strftime(format)

@app.route('/', methods=['GET', 'POST'])
def add_patient():
    if request.method == 'POST':
        # Extract data from form
        name = request.form['name']
        organ_type = request.form['organ_type']
        weight = float(request.form['weight'])
        number_of_fractions = int(request.form['number_of_fractions'])
        patient_type = request.form['patient_type']
        treatment_duration = int(request.form['treatment_duration'])

        # Create new Patient object
        new_patient = Patient(name=name, organ_type=organ_type, weight=weight,
                              number_of_fractions=number_of_fractions, patient_type=patient_type,
                              treatment_duration=treatment_duration)

        # Add new patient to database
        db.session.add(new_patient)
        db.session.commit()

        organ_type = request.form['organ_type']
        compatible_machines = organ_to_machine_map[organ_type]

        # Exclude VB1 and VB2 for patients over 70 kg
        if new_patient.weight > 70:
            compatible_machines = [machine for machine in compatible_machines if machine not in ['VB1', 'VB2']]

        compatible_machines = [machine for machine in compatible_machines if machine not in [0]]

        next_session_date = datetime.datetime.now()  # Adjust this to get the right starting datetime

        # Convert names to LinearAccelerator objects
        compatible_machines = LinearAccelerator.query.filter(
            LinearAccelerator.name.in_(compatible_machines),
        ).all()

        for _ in range(new_patient.number_of_fractions):
            next_session_date = get_next_session_date(next_session_date)

            # Count the appointments for each machine on the next_session_date
            appointment_counts = count_appointments_by_machine(next_session_date.date())

            # Filter and sort compatible machines by their appointment counts
            sorted_machines = sorted(
                compatible_machines,
                key=lambda machine: appointment_counts.get(machine.id, 0)
            )

            # Select the machine with the least appointments or randomly if there's a tie
            machine_name = sorted_machines[0]
            if sorted_machines and appointment_counts.get(sorted_machines[0].id, 0) == appointment_counts.get(
                    sorted_machines[1].id, 0):
                machine_name = random.choice(sorted_machines[:2])

            # machine_name = random.choice(compatible_machines)
            # machine_id = get_machine_id(machine_name)
            # print(f"Chosen machine: {machine_name}, ID: {machine_id}")

            appointment_time = find_suitable_appointment_time(machine_name)
            if not appointment_time:
                flash("Could not find a suitable appointment time.", 'error')
                continue

            new_appointment = Appointment(
                date=appointment_time,
                linear_accelerator_id=machine_name.id,
                patient_id=new_patient.id,
                notes="Scheduled automatically."
            )
            print(f"Appointment for patient {new_patient.id}, Machine ID: {new_appointment.linear_accelerator_id}")
            db.session.add(new_appointment)

        db.session.commit()
        return redirect(url_for('patients'))

    # Render the form template for GET request
    return render_template('add_patient.html')

@app.route('/patients')
def patients():
    all_patients = Patient.query.all()
    return render_template('patients.html', patients=all_patients)

@app.route('/appointments')
def appointments():
    patient_id = request.args.get('patient_id')
    if patient_id:
        all_appointments = Appointment.query.filter_by(patient_id=patient_id).all()
    else:
        all_appointments = Appointment.query.all()

    for appointment in all_appointments:
        print(f"Appointment ID: {appointment.id}, Machine Name: {appointment.linear_accelerator.name if appointment.linear_accelerator else 'No machine'}")

    return render_template('appointments.html', appointments=all_appointments)

@app.route('/clear_db')
def clear_db():
    try:
        # Delete all records from each table
        db.session.query(Appointment).delete()
        db.session.query(Patient).delete()
        db.session.query(LinearAccelerator).delete()
        db.session.commit()
        return "Database cleared!"
    except Exception as e:
        db.session.rollback()
        return f"Error occurred: {e}"

@app.route('/admin', methods=['GET', 'POST'])
def admin_control():
    if request.method == 'POST':
        machines = LinearAccelerator.query.all()
        for machine in machines:
            machine_id = str(machine.id)
            machine.is_active = 'is_active_' + machine_id in request.form

            # Convert operation times to time objects
            operation_start = request.form.get('operation_start_time_' + machine_id)
            operation_end = request.form.get('operation_end_time_' + machine_id)
            machine.operation_start_time = datetime.datetime.strptime(operation_start, '%H:%M').time() if operation_start else None
            machine.operation_end_time = datetime.datetime.strptime(operation_end, '%H:%M').time() if operation_end else None

            # Convert pause times to datetime objects
            pause_start = request.form.get('pause_start_time_' + machine_id)
            pause_end = request.form.get('pause_end_time_' + machine_id)
            machine.pause_start_time = datetime.datetime.strptime(pause_start, '%Y-%m-%dT%H:%M') if pause_start else None
            machine.pause_end_time = datetime.datetime.strptime(pause_end, '%Y-%m-%dT%H:%M') if pause_end else None

        db.session.commit()
        flash('Settings updated successfully!', 'success')  # Optional, for user feedback
        return redirect(url_for('admin_control'))

    machines = LinearAccelerator.query.all()
    return render_template('admin_control.html', machines=machines)

@app.route('/machine_stats/<int:machine_id>')
def machine_stats(machine_id):
    # Calculate stats for different intervals
    today = datetime.datetime.now().date()
    start_of_month = today.replace(day=1)
    start_of_year = today.replace(month=1, day=1)

    daily_stats = get_machine_usage_stats(machine_id, today, today)
    monthly_stats = get_machine_usage_stats(machine_id, start_of_month, today)
    yearly_stats = get_machine_usage_stats(machine_id, start_of_year, today)

    return render_template('machine_stats.html', daily_stats=daily_stats, monthly_stats=monthly_stats, yearly_stats=yearly_stats)

@app.route('/calendar')
def get_appointments():
    appointments = Appointment.query.all()  # or a more specific query as needed
    events = []
    for appointment in appointments:
        events.append({
            'title': f"{appointment.linear_accelerator.name} - {appointment.patient.name}",
            'start': appointment.date.strftime("%Y-%m-%dT%H:%M:%S"),
            'end': (appointment.date + datetime.timedelta(minutes=appointment.patient.treatment_duration)).strftime("%Y-%m-%dT%H:%M:%S"),
            'extendedProps': {
                'machine_type': appointment.linear_accelerator.type,
                'patient_name': appointment.patient.name
            }
        })
    return jsonify(events)

if __name__ == '__main__':
    populate_linear_accelerators()
    app.run(debug=True)