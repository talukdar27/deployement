
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session,send_from_directory
import jwt
import hashlib
import os
import mysql.connector
from mysql.connector import Error
from flask import flash
from PIL import Image
from werkzeug.utils import secure_filename
import base64
from flask import jsonify
import imageio 
import numpy as np
import io
import json
import time
from PIL import ImageOps
from moviepy.editor import ImageSequenceClip
from moviepy.editor import concatenate_videoclips
from moviepy.video.compositing.transitions import crossfadein, crossfadeout
from moviepy.video.compositing.concatenate import concatenate
from moviepy.video.fx.all import fadein, fadeout
from moviepy.video.VideoClip import ColorClip
from moviepy.video.compositing import CompositeVideoClip
from psycopg2.extensions import AsIs
from moviepy.editor import AudioFileClip
import psycopg2


app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', '9b47979a899d7a4c8f30cfc05da31a8058081c6e40b7b8a3')
connection = psycopg2.connect("postgresql://runtimeerror:76mHyzfr9k_rqrgRFhHQ8A@run-time-error-4066.7s5.aws-ap-south-1.cockroachlabs.cloud:26257/ChitrKatha?sslmode=verify-full")
cursor=connection.cursor()
# def create_db_connection():
#     try:
#         connection = mysql.connector.connect(
#             host='localhost',
#             user='root',
#             password='new_password',
#             database='ChitrKatha'
#         )
#         if connection.is_connected():
#             print(f"Connected to MySQL Server: {connection.get_server_info()}")
#             return connection
#     except Error as e:
#         print(f"Error: {e}")
#         return None

# db_connection = create_db_connection()

def create_user_table():
    try:
        cursor=connection.cursor()

        # Create user_info table if it doesn't exist
        create_table_query = '''
        CREATE TABLE IF NOT EXISTS user_info (
            id SERIAL PRIMARY KEY, -- Using SERIAL for auto-incrementing primary key
            name VARCHAR(100) NOT NULL,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
            )
        '''
        cursor.execute(create_table_query)

        print("user_info table created successfully")
    except Error as e:
        print(f"Error: {e}")
    finally:
        cursor.close()

cursor=connection.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS images (
    id SERIAL PRIMARY KEY, -- Using SERIAL for auto-incrementing primary key
    filename VARCHAR(255) NOT NULL,
    mimetype VARCHAR(50) NOT NULL,
    image_blob BYTEA NOT NULL, -- Using BYTEA for binary data
    username VARCHAR(255),
    metadata TEXT
    )''')
connection.commit()

def create_audio_table():
    try:
        cursor=connection.cursor()

        # Create audio table if it doesn't exist
        create_table_query = '''
        CREATE TABLE IF NOT EXISTS audio (
        id SERIAL PRIMARY KEY, -- Using SERIAL for auto-incrementing primary key
        filename VARCHAR(255) UNIQUE NOT NULL,
        audio_blob BYTEA NOT NULL, -- Using BYTEA for binary data
        metadata JSONB -- Using JSONB for storing JSON data
        )
        '''
        cursor.execute(create_table_query)

        print("audio table created successfully")
    except Error as e:
        print(f"Error: {e}")

def upload_audio_files():
    try:
        cursor=connection.cursor()

        # Get all .mp3 files in the static folder
        for filename in os.listdir('static'):
            if filename.endswith('.mp3'):
                # Check if file already exists in the audio table
                cursor.execute("SELECT * FROM audio WHERE filename = %s", (filename,))
                if cursor.fetchone() is not None:
                    print(f"File {filename} already exists in the database. Skipping.")
                    continue

                # Open file in binary mode
                with open(f'static/{filename}', 'rb') as file:
                    binary_data = file.read()

                # Prepare the metadata
                metadata = json.dumps({
                    'size': os.path.getsize(f'static/{filename}'),
                    'path': f'static/{filename}'
                })

                # Prepare the SQL query
                query = "INSERT INTO audio (filename, audio_blob, metadata) VALUES (%s, %s, %s)"

                # Execute the query
                cursor.execute(query, (filename, binary_data, metadata))

        # Commit the transaction
        connection.commit()

        print("The audio files were uploaded successfully.")

    except Error as e:
        print(f"Error: {e}")

    finally:
        cursor.close()

# Set the upload folder and allowed extensions
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Function to check if the file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def create_user(name, username, email, password):
    try:
        
        cursor = connection.cursor()

        insert_query = '''
        INSERT INTO user_info (name, username, email, password) VALUES (%s, %s, %s, %s)
        '''
        cursor.execute(insert_query, (name, username, email, password))

        connection.commit()
        print("User created successfully")
    except Error as e:
        print(f"Error: {e}")
        connection.rollback()
    finally:
        cursor.close()

def is_username_taken(username):
    try:
        cursor = connection.cursor()

        query = "SELECT * FROM user_info WHERE username = %s"
        cursor.execute(query, (username,))

        return cursor.fetchone() is not None
    except Error as e:
        print(f"Error: {e}")
    finally:
        cursor.close()

def is_email_registered(email):
    try:
        cursor = connection.cursor()

        query = "SELECT * FROM user_info WHERE email = %s"
        cursor.execute(query, (email,))

        return cursor.fetchone() is not None
    except Error as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
def get_user_by_username(username):
    try:
        cursor = connection.cursor()

        query = "SELECT * FROM user_info WHERE username = %s"
        cursor.execute(query, (username,))

        return cursor.fetchone()
    except Error as e:
        print(f"Error: {e}")
    finally:
        cursor.close()

def get_user_by_id(user_id):
    try:
        cursor = connection.cursor()

        query = "SELECT * FROM user_info WHERE id = %s"
        cursor.execute(query, (user_id,))

        return cursor.fetchone()
    except Error as e:
        print(f"Error: {e}")
    finally:
        cursor.close()

def get_current_user_name():
    if 'user_id' in session:
        user_id = session['user_id']
        user_data = get_user_by_id(user_id)
        if user_data:
            # Access the elements using indices instead of .get()
            return user_data[2]  # Assuming the 'name' attribute is at index 1
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

from moviepy.editor import AudioFileClip

@app.route('/create_video', methods=['POST'])
def create_video():
    username = get_current_user_name()
    transition = request.form.get('transition')
    selected_images = request.form.getlist('selected_images')
    selected_audio = request.form.get('audio')

    sizes = [(1920, 1080), (1280, 720), (854, 480), (640, 360), (426, 240)]  # 1080p, 720p, 480p, 360p, 240p
    image_data = {size: [] for size in sizes}

    try:
        for image in selected_images:
            # Run the query for each selected image
            cursor.execute('''
            SELECT image_blob, mimetype FROM images WHERE username = %s AND filename = %s
            ''', (username, image,))
            result = cursor.fetchone()

            if result is None:
                app.logger.error(f"No image found for filename {image}")
                continue

            for size in sizes:
                img = Image.open(io.BytesIO(base64.b64decode(result[0])))
                image_data[size].append(np.array(img))

        slideshow_paths = {}
        for size in sizes:
            # Create a .gif file from the images
            clips = [ImageSequenceClip([img], durations=[2]) for img in image_data[size]]  # 2 seconds per image

            # Add transitions
            if transition == 'fadein':
                clips = [clip.fadein(1) for clip in clips]  # 1 second fade-in on each clip
            elif transition == 'fadeout':
                clips = [clip.fadeout(1) for clip in clips]  # 1 second fade-out on each clip
            elif transition == 'crossfade':
                clips = [clips[i].crossfadein(1) if i != 0 else clips[i] for i in range(len(clips))]  # 1 second cross-fade on each clip except the first

            final_clip = concatenate_videoclips(clips, method="compose")

            # Retrieve the selected audio file
            cursor.execute('''
            SELECT audio_blob FROM audio WHERE filename = %s
            ''', (selected_audio,))
            result = cursor.fetchone()

            if result is not None:
                # Save the audio blob to a temporary file
                with open('temp_audio.mp3', 'wb') as audio_file:
                    audio_file.write(result[0])

                # Add the audio to the video
                audio = AudioFileClip('temp_audio.mp3')

                # Trim the audio to match the video duration
                audio = audio.subclip(0, final_clip.duration)

                final_clip = final_clip.set_audio(audio)

                final_clip.write_videofile(f'static/slideshow_{size[1]}.mp4', fps=24)

                slideshow_paths[size[1]] = f'/static/slideshow_{size[1]}.mp4'

        timestamp = time.time()
        return render_template('create_video.html', slideshow_paths=slideshow_paths, timestamp=timestamp)
    except Exception as e:
        # Log the error message
        app.logger.error(f"Error retrieving images: {str(e)}")
        # Return a user-friendly error message
        return "An error occurred while retrieving images", 500
    

def hash_password(password):
    # Use a strong hashing algorithm (e.g., SHA-256)
    return hashlib.sha256(password.encode()).hexdigest()
    
@app.route('/logout')
def logout():
    # Clear the user session data
    session.pop('user_id', None)
    # Redirect to the login page or any other desired page
    return redirect(url_for('login'))


@app.route('/get_user_details')
def get_user_details():
    try:
        cursor = connection.cursor(dictionary=True)

        # Select all users from the user_info table
        query = "SELECT * FROM user_info"
        cursor.execute(query)

        # Fetch all user details as a list of dictionaries
        user_details = cursor.fetchall()

        return jsonify(user_details)
    except Error as e:
        print(f"Error: {e}")
        return jsonify(error="Error fetching user details"), 500
    finally:
        cursor.close()

# def get_username_by_name(searched_name):
#     if 'user_id' in session:
#         # Assuming you have a 'user_info' table with 'name' and 'username' columns
#         user_query = "SELECT username FROM user_info WHERE name = %s"
        
#         try:
#             connection = db_connection
#             cursor = connection.cursor()

#             cursor.execute(query, (searched_name,))
#             result = cursor.fetchone()

#             if result:
#                 return result[0]  # Return the username
#         except Error as e:
#             print(f"Error: {e}")
#         finally:
#             cursor.close()

#     return None

@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        data = request.form.to_dict()
        name = data.get('name')
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirmPassword')

        # Check if password and confirm password match
        if password != confirm_password:
            flash('Password and Confirm Password do not match', 'error')
            return redirect(url_for('create_account'))

        # Check if username is already taken
        if is_username_taken(username):
            flash('Username is already taken', 'error')
            return redirect(url_for('create_account'))

        # Check if email is unique
        if is_email_registered(email):
           flash('Email is already registered. Please use a different email.', 'error')
           return redirect(url_for('create_account'))

        # Check if password is provided
        if not password:
            flash('Password is required', 'error')
            return redirect(url_for('create_account'))

        # Hash the password before storing it using hashlib
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Store user data in the database
        create_user(name, username, email, hashed_password)
        print("created",name, username, email, hashed_password)
        # Log in the user after creating the account
        user_data = get_user_by_username(username)
        print(type(user_data))
        print(user_data[0])
        session['user_id'] = user_data[0]

        # Redirect to the 'home' route after successful registration
        return redirect(url_for('home'))

    # If the request method is 'GET', render the 'create_account' template
    return render_template('create_account.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'images' not in request.files:
        return 'No files uploaded', 400

    files = request.files.getlist('images')
    uploaded_filenames = []
    user_name = get_current_user_name()
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Open the image and get metadata
            img = Image.open(file_path)
            metadata = img.info

            # Read the image file in binary mode and encode it as a base64 string
            with open(file_path, 'rb') as f:
                image_blob = base64.b64encode(f.read())

            # Insert metadata, image blob, and filename into the database
            cursor.execute('''
                INSERT INTO images (filename, mimetype, metadata, image_blob,username) VALUES (%s, %s, %s, %s, %s)
            ''', (filename, file.mimetype, str(metadata), image_blob,user_name))
            connection.commit()

            uploaded_filenames.append(filename)

    # Render the index.html template with the uploaded filenames
    return redirect(url_for('home'))
    # return render_template('home.html', success_message='Images uploaded successfully', uploaded_filenames=uploaded_filenames,user_name=user_name)

@app.route('/home/<username>')
def uploaded_file(username):
    user_name = get_current_user_name()
    try:
        cursor.execute('''
            SELECT image_blob, mimetype, filename FROM images WHERE username = %s
        ''', (username,))
        result = cursor.fetchall()

        if not result:
            return 'No image found for this user', 404

        images = [{'data': row[0].decode('utf-8'), 'mimetype': row[1], 'filename': row[2]} for row in result]

        return render_template('home.html', images=images, user_name=user_name)
    except Exception as e:
        # Log the error message
        app.logger.error(f"Error retrieving images: {str(e)}")
        # Return a user-friendly error message
        return "An error occurred while retrieving images", 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        print(f"Username: {username}, Password: {password}")

        if username == 'admin' and password == 'admin':
            return jsonify({'success': True, 'redirect': '/admin'})
            # Set the session for admin user

        user_data = get_user_by_username(username)
        print(f"user_data: {user_data}")
        print(hash_password(password))
        if username==user_data[2] and user_data[4] == hash_password(password):
            # Successful login
            session['user_id'] = user_data[0]
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Invalid username or password'}), 401
    else:
        # Render the login page for GET request
        return render_template('login.html')

@app.route('/home')
def home():
    user_name = get_current_user_name()
    if user_name:
        # return render_template('home.html', user_name=user_name)
        success_message = request.args.get('success')
        # try:
        cursor.execute('''
            SELECT image_blob, mimetype, filename FROM images WHERE username = %s
        ''', (user_name,))
        result = cursor.fetchall()
        images = []
        for row in result:
                byt = str(row[0])
                print(type(byt))
                print(str(row[0]))
                # image_data = base64.b64encode(byt).decode('utf-8')  # Convert image data to base64
                mimetype = row[1]
                filename = row[2]
                images.append({'data': byt, 'mimetype': mimetype, 'filename': filename})
        # print(images[0])
        return render_template('home.html', images=images, user_name=user_name)
        # except Exception as e:
        # # Log the error message
        #     app.logger.error(f"Error retrieving images: {str(e)}")
        # # Return a user-friendly error message 
        #     return "An error occurred while retrieving images", 500
        # return redirect(url_for('uploaded_file', username=user_name))
    else:
        flash('Please login first', 'info')
        return redirect(url_for('login'))

if __name__ == '__main__':
    create_user_table()
    create_audio_table()
    upload_audio_files() 
    app.run(debug=True)
