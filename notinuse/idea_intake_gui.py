import os
import json
import sys
from dotenv import load_dotenv
import anthropic
from anthropic import Anthropic
import re

# Load environment variables
load_dotenv()

# Get API key from environment
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "claude-3-opus-20240229")

try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox
    GUI_AVAILABLE = True
except ImportError:
    print("Tkinter is not available on this system. Using command-line version instead.")
    GUI_AVAILABLE = False

def extract_json_from_text(text):
    """Extract JSON from text that might contain markdown or other content."""
    # Try to parse the entire response as JSON first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON from markdown code blocks
    json_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
    matches = re.findall(json_pattern, text)
    
    if matches:
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
    
    # Try to find JSON-like content with regex (more aggressive approach)
    json_like_pattern = r'\{\s*"[^"]+"\s*:(?:[^{}]|(?R))*\}'
    matches = re.findall(json_like_pattern, text)
    
    if matches:
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
    
    # If all else fails, return None to indicate failure
    return None

def process_with_claude(idea):
    """Process the idea with Claude to get structured specifications"""
    print("\nProcessing your idea with Claude...\n")
    
    try:
        client = Anthropic(api_key=CLAUDE_API_KEY)
        
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=4096,
            messages=[
                {"role": "user", "content": f"""
                I have a rough idea for a project. Please help me structure it into a detailed specification.
                
                MY IDEA: {idea}
                
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
                
                Make sure your output is valid JSON that can be parsed. Use the triple backticks format with 'json' to ensure I can parse it correctly.
                """}
            ]
        )
        
        response_text = response.content[0].text
        specification = extract_json_from_text(response_text)
        
        if not specification:
            return {"error": "Failed to parse response from Claude as valid JSON. Raw response: " + response_text[:200] + "..."}
            
        return specification
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"error": str(e)}

def save_specification(specification):
    """Save the specification to a JSON file"""
    # Create specs directory if it doesn't exist
    os.makedirs("specs", exist_ok=True)
    
    filename = f"specs/{specification.get('project_title', 'project').lower().replace(' ', '_')}_spec.json"
    
    with open(filename, "w") as f:
        json.dump(specification, f, indent=2)
    
    print(f"\nSpecification saved to {filename}")
    return filename

def display_specification(specification):
    """Display the specification in a readable format"""
    if "error" in specification:
        print("\nThere was an error processing your idea:")
        print(specification["error"])
        return
    
    print("\n" + "="*50)
    print(f"         {specification.get('project_title', 'PROJECT SPECIFICATION')}")
    print("="*50)
    
    print(f"\nDescription: {specification.get('project_description', 'N/A')}")
    print(f"\nFor: {specification.get('target_users', 'N/A')}")
    
    print("\nKey Features:")
    for feature in specification.get('key_features', []):
        print(f"  - {feature.get('name')}: {feature.get('description')}")
    
    print(f"\nRecommended Tech Stack: {specification.get('technical_stack', 'N/A')}")
    
    print("\nMain Components:")
    for component in specification.get('components', []):
        print(f"  - {component}")
    
    print("\nMissing Information:")
    for info in specification.get('missing_info', []):
        print(f"  - {info}")

class IdeaIntakeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cursor AI Agent - Idea Intake")
        self.root.geometry("800x600")
        
        # Create a simple UI
        self.label = ttk.Label(root, text="Cursor AI Agent - Idea Intake System", font=("Arial", 16))
        self.label.pack(pady=20)
        
        self.desc = ttk.Label(root, text="Enter your project idea below:")
        self.desc.pack(pady=10)
        
        self.idea_text = scrolledtext.ScrolledText(root, height=10)
        self.idea_text.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        self.button = ttk.Button(root, text="Process with Claude", command=self.process_idea)
        self.button.pack(pady=20)
        
        self.status_label = ttk.Label(root, text="")
        self.status_label.pack(pady=10)
    
    def process_idea(self):
        idea = self.idea_text.get("1.0", tk.END).strip()
        
        if not idea:
            messagebox.showerror("Error", "Please enter your project idea first.")
            return
        
        self.status_label.config(text="Processing with Claude... Please wait.")
        self.root.update()
        
        specification = process_with_claude(idea)
        
        if "error" in specification:
            messagebox.showerror("Error", f"Error processing idea: {specification['error']}")
            self.status_label.config(text="Error occurred.")
            return
        
        filename = save_specification(specification)
        
        # Display results
        result_window = tk.Toplevel(self.root)
        result_window.title("Specification Result")
        result_window.geometry("800x600")
        
        title_label = ttk.Label(result_window, text=specification.get('project_title', 'PROJECT SPECIFICATION'), font=("Arial", 16, "bold"))
        title_label.pack(pady=20)
        
        result_text = scrolledtext.ScrolledText(result_window, wrap=tk.WORD)
        result_text.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        # Insert specification details
        result_text.insert(tk.END, f"Description: {specification.get('project_description', 'N/A')}\n\n")
        result_text.insert(tk.END, f"For: {specification.get('target_users', 'N/A')}\n\n")
        
        result_text.insert(tk.END, "Key Features:\n")
        for feature in specification.get('key_features', []):
            result_text.insert(tk.END, f"- {feature.get('name')}: {feature.get('description')}\n")
        
        result_text.insert(tk.END, f"\nRecommended Tech Stack: {specification.get('technical_stack', 'N/A')}\n\n")
        
        result_text.insert(tk.END, "Main Components:\n")
        for component in specification.get('components', []):
            result_text.insert(tk.END, f"- {component}\n")
        
        result_text.insert(tk.END, "\nMissing Information:\n")
        for info in specification.get('missing_info', []):
            result_text.insert(tk.END, f"- {info}\n")
        
        result_text.config(state=tk.DISABLED)
        
        save_label = ttk.Label(result_window, text=f"Specification saved to {filename}")
        save_label.pack(pady=10)
        
        close_button = ttk.Button(result_window, text="Close", command=result_window.destroy)
        close_button.pack(pady=10)
        
        self.status_label.config(text=f"Specification generated and saved to {filename}")

def command_line_mode():
    """Run in command-line mode if GUI is not available"""
    print("\n" + "="*50)
    print("        CURSOR AI AGENT - IDEA INTAKE")
    print("="*50)
    print("\nThis tool will help structure your rough ideas into specifications")
    print("that can be turned into code by Cursor.")
    
    print("\nWhat's your rough idea for a project or application?")
    print("Describe it in as much or as little detail as you have:")
    idea = input("\n> ")
    
    specification = process_with_claude(idea)
    display_specification(specification)
    save_specification(specification)

if __name__ == "__main__":
    if GUI_AVAILABLE:
        try:
            root = tk.Tk()
            app = IdeaIntakeApp(root)
            root.mainloop()
        except Exception as e:
            print(f"Error starting GUI: {str(e)}")
            print("Falling back to command-line mode...")
            command_line_mode()
    else:
        command_line_mode() 