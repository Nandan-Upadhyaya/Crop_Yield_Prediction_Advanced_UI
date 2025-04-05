"""
NOTE: This file will be moved to the backend directory.
You can run it from there or keep using it here for backward compatibility.
"""
from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
import numpy as np
import pickle
import sklearn
from pymongo import MongoClient
from datetime import datetime
import os
print(sklearn.__version__)

# MongoDB Setup
client = MongoClient('mongodb://localhost:27017/')
db = client['crop_yield_db']
predictions_collection = db['predictions']

# Check if MongoDB connection is working and database exists
def check_mongodb_connection():
    try:
        # Check connection
        client.server_info()
        print("✅ Successfully connected to MongoDB server")
        
        # Check if our database is in the list of database names
        database_names = client.list_database_names()
        if 'crop_yield_db' in database_names:
            print(f"✅ Database 'crop_yield_db' exists")
        else:
            print(f"ℹ️ Database 'crop_yield_db' doesn't exist yet. It will be created when data is inserted.")
        
        # Check collections in the database
        collection_names = db.list_collection_names()
        if 'predictions' in collection_names:
            print(f"✅ Collection 'predictions' exists")
            print(f"ℹ️ Number of records in 'predictions' collection: {predictions_collection.count_documents({})}")
        else:
            print(f"ℹ️ Collection 'predictions' doesn't exist yet. It will be created when data is inserted.")
            
        return True
    except Exception as e:
        print(f"❌ MongoDB connection error: {e}")
        return False

#loading models
dtr = pickle.load(open('dtr.pkl','rb'))
preprocessor = pickle.load(open('preprocessor.pkl','rb'))

#flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/predict", methods=['POST'])
def predict():
    if request.method == 'POST':
        # Check if request is coming from React (JSON) or form
        if request.is_json:
            data = request.get_json()
            Year = data['Year']
            average_rain_fall_mm_per_year = data['average_rain_fall_mm_per_year']
            pesticides_tonnes = data['pesticides_tonnes']
            avg_temp = data['avg_temp']
            Area = data['Area']
            Item = data['Item']
        else:
            # Handle form data (original behavior)
            Year = request.form['Year']
            average_rain_fall_mm_per_year = request.form['average_rain_fall_mm_per_year']
            pesticides_tonnes = request.form['pesticides_tonnes']
            avg_temp = request.form['avg_temp']
            Area = request.form['Area']
            Item = request.form['Item']

        features = np.array([[Year, average_rain_fall_mm_per_year, pesticides_tonnes, avg_temp, Area, Item]], dtype=object)
        transformed_features = preprocessor.transform(features)
        prediction = dtr.predict(transformed_features).reshape(1, -1)
        
        # Store prediction in MongoDB
        prediction_record = {
            'timestamp': datetime.now(),
            'features': {
                'Year': Year,
                'average_rain_fall_mm_per_year': average_rain_fall_mm_per_year,
                'pesticides_tonnes': pesticides_tonnes,
                'avg_temp': avg_temp,
                'Area': Area,
                'Item': Item
            },
            'prediction': prediction.tolist()[0][0]
        }
        predictions_collection.insert_one(prediction_record)
        
        # If request is from React, return JSON
        if request.is_json:
            return jsonify({"prediction": prediction.tolist()})
        
        # Otherwise return the HTML template
        return render_template('index.html', prediction=prediction)

@app.route('/history', methods=['GET'])
def get_history():
    """Endpoint to retrieve prediction history"""
    # Get the last 10 predictions
    history = list(predictions_collection.find({}, {'_id': 0}).sort('timestamp', -1).limit(10))
    
    # Convert datetime objects to string for JSON serialization
    for record in history:
        record['timestamp'] = record['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
    
    return jsonify({'history': history})

@app.route('/check-db', methods=['GET'])
def check_db():
    """Endpoint to check database status"""
    is_connected = check_mongodb_connection()
    
    # Get collection stats if connected
    stats = {}
    if is_connected:
        try:
            stats['record_count'] = predictions_collection.count_documents({})
            stats['database_exists'] = 'crop_yield_db' in client.list_database_names()
            stats['collection_exists'] = 'predictions' in db.list_collection_names()
        except Exception as e:
            stats['error'] = str(e)
    
    return jsonify({
        'connected': is_connected,
        'database': 'crop_yield_db',
        'collection': 'predictions',
        'stats': stats
    })

if __name__ == "__main__":
    # Check MongoDB connection on startup
    check_mongodb_connection()
    app.run(debug=True)