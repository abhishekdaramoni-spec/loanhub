import sys
import os

# Add root directory to sys.path to resolve the 'app' module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.utils.extensions import db
from app.utils.seeder import seed_default_data

def run_seeder():
    # Load development environment configurations
    app = create_app('development')
    with app.app_context():
        print("Dropping existing tables and recreating database schemas...")
        db.drop_all()
        db.create_all()
        
        print("Seeding default application settings, rates, and testing credentials...")
        seed_default_data()
        print("Development database tables initialized and seeded successfully!")

if __name__ == '__main__':
    run_seeder()
