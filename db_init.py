#!/usr/bin/env python3
"""
Database initialization script for FastAPI JWT Auth application.

This script creates the database tables and populates them with sample data
including users with different roles and sample employees.

Usage:
    python db_init.py

Environment Variables:
    SQLITE_DB_PATH: Path to the SQLite database file (default: "db.sqlite3")
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from models import Base, User, Employee
import bcrypt

def main():
    """Main function to initialize the database."""
    try:
        load_dotenv()
        sqlite_db_path = os.getenv("SQLITE_DB_PATH", "db.sqlite3")
        
        print(f"Initializing database at: {sqlite_db_path}")
        
        if not sqlite_db_path:
            raise ValueError("SQLITE_DB_PATH environment variable is not set.")
    except Exception as e:
        print(f"Error loading environment: {e}")
        sys.exit(1)


    # Database configuration
    ROLES = {"User": 2001, "Editor": 1984, "Admin": 5150}
    employees = [
        {"id": 1, "firstname": "Dave", "lastname": "Gray"},
        {"id": 2, "firstname": "John", "lastname": "Smith"},
    ]
    users = [
        {"username": "admin", "password": "admin", "roles": "2001,1984,5150"},
        {"username": "user1", "password": "user1pass", "roles": "2001"},
        {"username": "user2", "password": "user2pass", "roles": "2001,1984"},
    ]

    try:
        # Create an SQLite database
        print("Creating database engine...")
        engine = create_engine(f"sqlite:///{sqlite_db_path}", echo=False)

        # Create all tables in the database
        print("Creating database tables...")
        Base.metadata.create_all(engine)

        # Create a configured "Session" class
        Session = sessionmaker(bind=engine)

        # Create a session
        session = Session()

        # Add users with hashed passwords
        print("Adding users...")
        users_added = 0
        for user in users:
            if not session.query(User).filter_by(username=user["username"]).first():
                hashed_password = bcrypt.hashpw(user["password"].encode('utf-8'), bcrypt.gensalt())
                new_user = User(
                    username=user["username"],
                    password=hashed_password,
                    roles=user["roles"],
                )
                session.add(new_user)
                users_added += 1
            else:
                print(f"  User '{user['username']}' already exists, skipping...")
        
        session.commit()
        if users_added > 0:
            print(f"  {users_added} users added successfully.")
        else:
            print("  No new users to add.")

        # Add employees
        print("Adding employees...")
        employees_added = 0
        for emp in employees:
            if not session.query(Employee).filter_by(id=emp["id"]).first():
                new_employee = Employee(
                    id=emp["id"], firstname=emp["firstname"], lastname=emp["lastname"]
                )
                session.add(new_employee)
                employees_added += 1
            else:
                print(f"  Employee '{emp['firstname']} {emp['lastname']}' (ID: {emp['id']}) already exists, skipping...")
        
        session.commit()
        if employees_added > 0:
            print(f"  {employees_added} employees added successfully.")
        else:
            print("  No new employees to add.")

        # Close the session
        session.close()
        print("✅ Database initialized successfully!")
        
        # Display summary
        session = Session()
        user_count = session.query(User).count()
        employee_count = session.query(Employee).count()
        session.close()
        
        print(f"\nDatabase Summary:")
        print(f"  📊 Total users: {user_count}")
        print(f"  👥 Total employees: {employee_count}")
        print(f"  💾 Database file: {sqlite_db_path}")
        
        print(f"\nSample login credentials:")
        for user in users:
            print(f"  Username: {user['username']} | Password: {user['password']} | Roles: {user['roles']}")

    except SQLAlchemyError as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
