#!/usr/bin/env python3
import os
from app.src import create_app, db

app = create_app()

@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    print("Database initialized!")

@app.cli.command()
def reset_db():
    """Reset the database (WARNING: This will delete all data!)."""
    db.drop_all()
    db.create_all()
    print("Database reset!")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)