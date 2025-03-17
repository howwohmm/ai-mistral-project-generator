"""
Main entry point for Streamlit Cloud deployment.
This file is automatically detected by Streamlit Cloud.
"""
import sys
import os

# Add root directory to import path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and run the actual application
from src.frontend.app import main

# Execute the main function
if __name__ == "__main__":
    main() 