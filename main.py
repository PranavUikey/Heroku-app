import pandas as pd
import gspread
import numpy as np

from oauth2client.service_account import ServiceAccountCredentials

from flask import Flask, render_template, flash, redirect, url_for, request
from flask_bootstrap import Bootstrap

from flask_wtf import FlaskForm 

from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length



app = Flask(__name__)
app.config['SECRET_KEY'] = 'Thisissupposedtobesecret!'
bootstrap = Bootstrap(app)


scope = ["https://spreadsheets.google.com/feeds",
        'https://www.googleapis.com/auth/spreadsheets',
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)



LEADERBOARD = '05-01-2019'
write_sheet = client.open(LEADERBOARD).sheet1
COLUMNS = write_sheet.row_values(1)

class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])

def email_to_name(email):
    database = pd.read_csv('students.csv')
    try:
        name = database[database['Email'] == email.strip()]['Name'].values[0]
    except:
        name = None
    return name

def read_from_sheet(email_id, test_id):
    """
    Returns the score of email_id for test_id.
    If return value is None, the process was unsuccessful
    """

    email_id = email_id.lower().strip()

    number_to_test = {
        '1':'Quiz1',
        '2':'Quiz2',
        '3':'A2',
        '4':'Quiz3',
        '5':'A3',
        '6':'Quiz4',
        '7':'A4'
    }

    sheets = {
        'Quiz1': 'Python For Data Science Course (Weekend Nov-19) Quiz-1 (Responses)',
        'Quiz2':'Python For Data Science Course (Weekend Nov-19) Quiz-2 (Responses)',
        'A2':'Python For Data Science Course (Weekend Nov-19) Assignment- 2 (Responses)',
        'Quiz3':'Python For Data Science Course (Weekend Nov-19) Quiz-3 (Responses)',
        'A3':'Python For Data Science Course (Weekend Nov-19) Assignment- 3 (Responses)',
        'Quiz4':'Python For Data Science Course (Weekend Nov-19) Quiz-4 (Responses)',
        'A4':'Python For Data Science Course (Weekend Nov-19) Assignment- 4 (Responses)'
    }
    
    col_name = number_to_test[test_id]
    to_read = sheets[col_name]
    read_sheet = client.open(to_read).sheet1 

    # Reading score from responses sheet
    read_cols = read_sheet.row_values(1)
    email_key = 'Email Address' if 'Email Address' in read_cols else 'Email address'
    
    try:
        read_cell = read_sheet.find(email_id)
        score_row_id = read_cell.row
    except gspread.exceptions.CellNotFound:
        print('Email: {} not found in {} submission sheet!'.format(email_id,number_to_test[test_id]))
        return None

    score_col_id = read_cols.index('Score') + 1 # 1 indexed
    score = read_sheet.cell(score_row_id, score_col_id).value.split('/')[0]

    # Writing score to leaderboard
    col_id = COLUMNS.index(col_name) + 1 # 1 indexed
    name = email_to_name(email_id)

    if name is None:
        print('Name not found in database!')
        return None

    try:
        # Checking if name exists in leaderboard
        name_cell = write_sheet.find(name)
        row_id = name_cell.row
    except gspread.exceptions.CellNotFound as e:
        # Creating a new row with new name
        row_id = len(write_sheet.get_all_values()) + 1
        write_sheet.update_cell(row_id, COLUMNS.index('Name') + 1, name)

    write_sheet.update_cell(row_id, col_id, int(score))

    return score

def append_row(row):
    database = pd.read_csv('students.csv')
    database = database.append(row, ignore_index=True)
    database.to_csv('students.csv', index=False)

def delete_row(email):
    database = pd.read_csv('students.csv')
    database = database[database.Email != email]
    database.to_csv('students.csv', index=False)

@app.route('/add_std', methods=['POST'])
def add_std():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        number = request.form['number']
        append_row({'Name': name, 'Email': email, 'Number': number})
        # flask('Added '+ name)
        return redirect(url_for('homepage'))
    else:
        return redirect(url_for('homepage'))

@app.route('/delete/<email>')
def delete(email):
    delete_row(email)
    return redirect(url_for('homepage'))

@app.route('/submit/<student_id>')
def submit(student_id):
    *student, id = student_id.split('_')
    student = '_'.join(student)
    print('Submitting {} for {}'.format(id,student))
    print('Score: {}'.format(read_from_sheet(email_id=student, test_id=id)))
    return redirect(url_for('homepage'))

@app.route('/add')
def homepage():
    database = pd.read_csv('students.csv')
    database.Name = database.Name.str.replace(' ', '-')
    students = list(database.T.to_dict().values())

    return render_template('main.html', students = students)



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        info = list(request.form.values())[1:]
        # print()
        print(info)
        if (info[1]=='Admin') and (info[0]=='aiadvadmin'):
           return redirect(url_for('homepage'))
        else:
           return 'Wrong Password'

    return render_template('login.html', form=form)

if __name__ == "__main__":

    app.run(debug = True)