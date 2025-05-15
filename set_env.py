# set_env.py
import os

def set_environment_variables():
    # Dictionary of environment variables
    env_vars = {
        'COPYLEAKS_EMAIL': 'stanlymelis1@gmail.com',
        'COPYLEAKS_API_KEY': 'e9c8a617-9516-4441-9dea-9afb641e35cb',
    }

    # Set each environment variable
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"Set {key}")

    print("Environment variables set successfully!")

if __name__ == "__main__":
    set_environment_variables()