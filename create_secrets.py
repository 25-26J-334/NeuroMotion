"""
Helper script to create .streamlit/secrets.toml file for SQLite
Optional - SQLite works without secrets file (uses default path)
"""
import os
from pathlib import Path

def create_secrets_file():
    """Create secrets.toml file with user input for SQLite database path"""
    print("=" * 50)
    print("Streamlit Secrets File Setup (SQLite)")
    print("=" * 50)
    
    print("\nNote: SQLite database works without a secrets file.")
    print("If you don't create one, the database will be created")
    print("in the source directory as 'athlete_trainer.db'")
    
    use_custom = input("\nDo you want to specify a custom database path? (y/n) [n]: ").strip().lower()
    
    if use_custom != 'y':
        print("\n✅ No secrets file needed. Database will be created automatically.")
        print("   Location: source/athlete_trainer.db")
        return
    
    # Get custom database path
    print("\nEnter custom database path:")
    db_path = input("Database path [athlete_trainer.db]: ").strip() or "athlete_trainer.db"
    
    # Create .streamlit directory
    streamlit_dir = Path(".streamlit")
    streamlit_dir.mkdir(exist_ok=True)
    
    # Create secrets.toml
    secrets_file = streamlit_dir / "secrets.toml"
    
    content = f"""[sqlite]
database_path = "{db_path}"
"""
    
    with open(secrets_file, 'w') as f:
        f.write(content)
    
    print(f"\n✅ Secrets file created at: {secrets_file.absolute()}")
    print("\nNext steps:")
    print("1. Run: python setup_database.py (to create the database)")
    print("2. Run: streamlit run app.py")

if __name__ == "__main__":
    create_secrets_file()
