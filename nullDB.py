import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# Firebase database URL
# DATABASE_URL = "https://natalibraudecloud-default-rtdb.europe-west1.firebasedatabase.app/"
DATABASE_URL = "https://wolf-db-bfac4-default-rtdb.europe-west1.firebasedatabase.app/"


def null_database():
    try:
        # Initialize Firebase Admin SDK (assuming you have a service account key)
        # cred = credentials.Certificate("serviceAccountKey.json")
        cred = credentials.Certificate("wolf.json")
        firebase_admin.initialize_app(cred, {
            'databaseURL': DATABASE_URL
        })  
        
        # Get reference to root of database
        ref = db.reference('/')
        
        # Set null/empty value at root to clear entire database
        ref.set({})
        
        print("Database successfully cleared!")
        
    except Exception as e:
        print(f"Error clearing database: {e}")

if __name__ == "__main__":
    null_database()