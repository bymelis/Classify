from Classify import app, db
import os
from set_env import set_environment_variables

def reset_database():
    with app.app_context():
        # Drop all tables
        db.drop_all()

        # Get the database file path
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')

        # Remove the database file if it exists
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Removed existing database: {db_path}")

        # Create all tables
        db.create_all()
        print("Database has been reset and recreated with the current schema!")

if __name__ == "__main__":
    # Set environment variables first
    set_environment_variables()
    # Then reset the database
    reset_database()