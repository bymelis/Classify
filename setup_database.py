import os
from flask_migrate import init, migrate, upgrade
from Classify import app, db


def setup_database():
    try:
        # Set the Flask app environment variable
        os.environ['FLASK_APP'] = 'Classify'

        # Initialize migrations folder if it doesn't exist
        print("Initializing migrations...")
        with app.app_context():
            init()

        # Create migration
        print("Creating migration...")
        with app.app_context():
            migrate(directory='migrations', message='Initial migration')

        # Apply migration
        print("Applying migration...")
        with app.app_context():
            upgrade(directory='migrations')

        print("Database setup completed successfully!")

    except Exception as e:
        print(f"An error occurred during database setup: {str(e)}")


if __name__ == "__main__":
    setup_database()