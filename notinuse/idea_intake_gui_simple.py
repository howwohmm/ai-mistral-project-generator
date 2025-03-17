import os
import json
import tkinter as tk
from tkinter import scrolledtext, Button, Label, messagebox
from dotenv import load_dotenv
import anthropic
from anthropic import Anthropic

# Load environment variables
load_dotenv()

# Get API key from environment
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "claude-3-opus-20240229")

def process_idea(idea_text, status_label, root):
    """Process the idea with Claude"""
    if not idea_text.strip():
        messagebox.showerror("Error", "Please enter your idea first")
        return
    
    status_label.config(text="Processing with Claude... Please wait.")
    root.update()
    
    try:
        client = Anthropic(api_key=CLAUDE_API_KEY)
        
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=4096,
            messages=[
                {"role": "user", "content": f"""
                I have a rough idea for a project. Please help me structure it into a detailed specification.
                
                MY IDEA: {idea_text}
                
                Provide a response as a JSON object with these fields:
                1. project_title: A catchy name for the project
                2. project_description: A brief description of what it does
                3. target_users: Who will use this application
                4. key_features: An array of 3-5 main features (each with name and description)
                5. technical_stack: Recommended technologies to use
                6. components: Main components or files needed
                7. data_model: Any data structures or models needed
                8. api_endpoints: For web/mobile apps, any API endpoints needed
                9. user_interface: Brief description of key UI elements
                10. missing_info: What other information would be helpful to know
                
                Make sure your output is valid JSON that can be parsed.
                """}
            ]
        )
        
        response_text = response.content[0].text
        
        # Try to parse JSON from the response
        try:
            # First try to parse the entire response as JSON
            specification = json.loads(response_text)
        except json.JSONDecodeError:
            # If that fails, try to extract JSON from markdown code blocks
            import re
            json_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
            matches = re.findall(json_pattern, response_text)
            
            if matches:
                for match in matches:
                    try:
                        specification = json.loads(match)
                        break
                    except json.JSONDecodeError:
                        continue
            else:
                raise Exception("Could not parse Claude's response as valid JSON")
        
        # Save specification
        os.makedirs("specs", exist_ok=True)
        filename = f"specs/{specification.get('project_title', 'project').lower().replace(' ', '_')}_spec.json"
        with open(filename, "w") as f:
            json.dump(specification, f, indent=2)
        
        # Show results
        result_text = f"""
Title: {specification.get('project_title', 'N/A')}

Description: {specification.get('project_description', 'N/A')}

Target Users: {specification.get('target_users', 'N/A')}

Key Features:
"""
        for feature in specification.get('key_features', []):
            result_text += f"- {feature.get('name')}: {feature.get('description')}\n"
            
        result_text += f"\nTech Stack: {specification.get('technical_stack', 'N/A')}"
        
        messagebox.showinfo("Specification Generated", 
                           f"Specification has been generated and saved to {filename}\n\n{result_text}")
        
        status_label.config(text=f"Specification saved to {filename}")
        
    except Exception as e:
        messagebox.showerror("Error", f"Error: {str(e)}")
        status_label.config(text="Error occurred")

# Main window setup
root = tk.Tk()
root.title("Cursor AI Agent - Simple")
root.geometry("600x400")

# Add widgets
Label(root, text="Cursor AI Agent - Idea Intake", font=("Arial", 16)).pack(pady=10)
Label(root, text="Enter your project idea:").pack(pady=5)

idea_entry = scrolledtext.ScrolledText(root, height=10)
idea_entry.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

status_label = Label(root, text="")
status_label.pack(pady=5)

process_button = Button(
    root, 
    text="Process with Claude", 
    command=lambda: process_idea(idea_entry.get("1.0", tk.END), status_label, root)
)
process_button.pack(pady=10)

# Start the event loop
if __name__ == "__main__":
    root.mainloop() 