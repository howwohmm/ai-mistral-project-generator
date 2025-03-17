import streamlit as st
import requests
import json
import subprocess
import webbrowser
from pathlib import Path
import os
import time
import shutil
from dotenv import load_dotenv

class AICreativeCollaborator:
    def __init__(self):
        # Use environment variable for API URL with fallback to local development
        load_dotenv()
        
        # For web deployment: use environment variable for backend URL
        self.api_url = os.getenv("BACKEND_API_URL", "http://localhost:8000")
        
        # Add option to override with Streamlit secrets if available
        try:
            self.api_url = st.secrets.get("BACKEND_API_URL", self.api_url)
        except:
            pass
            
        st.sidebar.info(f"🔌 Connected to API: {self.api_url}")
        
        self.cursor_path = "/Applications/Cursor.app/Contents/MacOS/Cursor"
        # Define timeouts as class constants
        self.CHAT_TIMEOUT = 300  # 5 minutes for chat
        self.PRD_TIMEOUT = 600   # 10 minutes for PRD generation
        self.PROJECT_TIMEOUT = 60 # 1 minute for project creation

    def initialize_session(self):
        if "messages" not in st.session_state:
            st.session_state.messages = []
            # Don't add any system messages - let backend handle this
        if "current_phase" not in st.session_state:
            st.session_state.current_phase = "ideation"
        if "project_spec" not in st.session_state:
            st.session_state.project_spec = {}
        if "project_links" not in st.session_state:
            st.session_state.project_links = {}

    def chat_with_ai(self, messages):
        try:
            with st.spinner("Getting response from Mistral..."):
                # Only add user messages, let backend handle system message
                user_messages = []
                for msg in messages:
                    # Skip any existing system messages from the frontend
                    if msg["role"] != "system":
                        user_messages.append({"role": msg["role"], "content": msg["content"]})
                
                print(f"Sending {len(user_messages)} messages to backend")
                
                # Send request to backend API
                response = requests.post(
                    f"{self.api_url}/chat",
                    json={"messages": user_messages},
                    timeout=self.CHAT_TIMEOUT
                )
                
                if response.status_code == 500:
                    error_detail = response.json().get("detail", "Unknown error")
                    st.error(f"Server error: {error_detail}")
                    return None
                    
                response.raise_for_status()
                result = response.json()
                print(f"Received response: {result['response'][:100]}...")
                return result["response"]
        except requests.exceptions.ConnectionError:
            st.error(f"Could not connect to the backend server at {self.api_url}. Please ensure it's running.")
            return None
        except requests.exceptions.Timeout:
            st.error("Request timed out. Mistral is taking longer than expected to respond.")
            return None
        except requests.exceptions.RequestException as e:
            st.error(f"Error communicating with backend: {str(e)}")
            return None

    def generate_prd(self, messages):
        try:
            with st.spinner("Generating PRD with Mistral... This may take a few minutes."):
                # We don't need to add a system message - backend will handle that
                response = requests.post(
                    f"{self.api_url}/generate-prd",
                    json={"messages": [{"role": m["role"], "content": m["content"]} for m in messages]},
                    timeout=self.PRD_TIMEOUT
                )
                
                if response.status_code == 500:
                    error_detail = response.json().get("detail", "Unknown error")
                    st.error(f"Server error: {error_detail}")
                    return None
                    
                response.raise_for_status()
                prd_json = response.json()
                
                # Store project links if available
                if "projectLinks" in prd_json:
                    st.session_state.project_links = prd_json["projectLinks"]
                
                return prd_json
                
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to the backend server. Please ensure it's running.")
            return None
        except requests.exceptions.Timeout:
            st.error("Request timed out. PRD generation is taking longer than expected (>10 minutes).")
            return None
        except requests.exceptions.RequestException as e:
            st.error(f"Error generating PRD: {str(e)}")
            return None

    def create_cursor_project(self, spec):
        try:
            # First, get a project name from the user
            st.subheader("Create Project")
            project_name = st.text_input("Enter project name:", value=spec['title'].lower().replace(' ', '_'))
            
            if not project_name:
                st.warning("Please enter a project name to continue")
                return None
                
            # Only proceed when the user confirms
            if not st.button("Create Project Now", type="primary"):
                return None
                
            with st.spinner("Creating project..."):
                # First, add the port 3000 to the project links
                if "projectLinks" in spec:
                    spec["projectLinks"]["frontend"] = "http://localhost:3000"
                    spec["projectLinks"]["backend"] = "http://localhost:3001"
                
                response = requests.post(
                    f"{self.api_url}/create-project",
                    json=spec,
                    timeout=self.PROJECT_TIMEOUT
                )
                response.raise_for_status()
                result = response.json()
                project_dir = result["project_dir"]
                
                # Store project links with port 3000
                st.session_state.project_links = {
                    "project_dir": project_dir,
                    "frontend": "http://localhost:3000",
                    "backend": "http://localhost:3001"
                }
                
                # Check if running on Streamlit Cloud
                is_web_deployment = ('STREAMLIT_SHARING' in os.environ or
                                    'STREAMLIT_SERVER_HEADLESS' in os.environ or
                                    'WEBSITE_HOSTNAME' in os.environ)
                
                if is_web_deployment:
                    # Create a ZIP file for download instead of opening Cursor
                    st.success("Project created! Download it below:")
                    
                    # For web deployment - create a ZIP file for downloading
                    import zipfile
                    import io
                    
                    # Create a BytesIO object
                    zip_buffer = io.BytesIO()
                    
                    # Creating the ZIP file
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        for root, dirs, files in os.walk(project_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                # Calculate the relative path
                                rel_path = os.path.relpath(file_path, project_dir)
                                zip_file.write(file_path, os.path.join(project_name, rel_path))
                    
                    # Reset buffer position to start
                    zip_buffer.seek(0)
                    
                    # Provide download button
                    st.download_button(
                        label="Download Project as ZIP",
                        data=zip_buffer,
                        file_name=f"{project_name}.zip",
                        mime="application/zip"
                    )
                    
                    return project_dir
                    
                else:
                    # Local deployment - Create a new Cursor project using command line
                    try:
                        # First close any existing Cursor instances to avoid conflicts
                        subprocess.run(["pkill", "-f", "Cursor"], stderr=subprocess.DEVNULL)
                        subprocess.run(["sleep", "1"])
                        
                        # Create a folder with just the user-provided name (no timestamp)
                        new_project_dir = Path(os.path.expanduser("~")) / "Documents" / "cursor_projects" / project_name
                        
                        # Create parent directories if they don't exist
                        new_project_dir.parent.mkdir(parents=True, exist_ok=True)
                        
                        # If directory exists, remove it to avoid conflicts
                        if new_project_dir.exists():
                            shutil.rmtree(new_project_dir)
                            
                        new_project_dir.mkdir(exist_ok=True)
                        
                        # Copy files from project_dir to new_project_dir
                        for item in Path(project_dir).glob('*'):
                            if item.is_file():
                                shutil.copy2(item, new_project_dir)
                            elif item.is_dir():
                                shutil.copytree(item, new_project_dir / item.name)
                        
                        # Create the IMPLEMENT_PRD.txt with the FULL PRD content
                        prd_content = f"""# {spec['title']} - PRD

## Please implement this PRD in a new project
Start a development server on port 3000.

## Project Overview
{spec['description']}

## Features
"""
                        # Add features
                        for feature in spec['features']:
                            prd_content += f"- {feature['name']} ({feature['priority']}): {feature['description']}\n"
                        
                        prd_content += "\n## Technologies\n"
                        for tech in spec['technologies']:
                            prd_content += f"- {tech['name']}: {tech['purpose']}\n"
                        
                        prd_content += f"\n## Architecture\nType: {spec['architecture']['type']}\n\nComponents:\n"
                        for comp in spec['architecture']['components']:
                            prd_content += f"- {comp['name']}: {comp['purpose']}\n"
                            prd_content += f"  Interactions: {', '.join(comp['interactions'])}\n"
                        
                        prd_content += "\n## Implementation Plan\n"
                        for i, phase in enumerate(spec['implementationPlan']):
                            prd_content += f"### Phase {i+1}: {phase['phase']} ({phase['duration']})\n"
                            for task in phase['tasks']:
                                prd_content += f"- {task['name']} ({task['duration']})\n"
                        
                        # Write the full PRD content to IMPLEMENT_PRD.txt
                        with open(new_project_dir / "IMPLEMENT_PRD.txt", "w") as f:
                            f.write(prd_content)
                        
                        # Add a package.json with port 3000 configured
                        package_json = {
                            "name": project_name,
                            "version": "1.0.0",
                            "description": spec["description"],
                            "main": "index.js",
                            "scripts": {
                                "start": "node server.js",
                                "dev": "nodemon server.js"
                            },
                            "dependencies": {},
                            "devDependencies": {},
                            "port": 3000
                        }
                        
                        with open(new_project_dir / "package.json", "w") as f:
                            json.dump(package_json, f, indent=2)
                        
                        # Create a basic server file that uses port 3000
                        server_js = """const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 3000;

const server = http.createServer((req, res) => {
  res.writeHead(200, {'Content-Type': 'text/html'});
  res.end('<h1>Project Implementation Server</h1><p>This project is running on port 3000</p>');
});

server.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}/`);
});
"""
                        with open(new_project_dir / "server.js", "w") as f:
                            f.write(server_js)
                        
                        # Open in a NEW Cursor window with absolute path
                        subprocess.Popen([self.cursor_path, "--new-window", str(new_project_dir.absolute())])
                        
                        # Update project_dir to the new location
                        st.session_state.project_links["project_dir"] = str(new_project_dir.absolute())
                        
                        return str(new_project_dir.absolute())
                    except Exception as e:
                        st.error(f"Error setting up Cursor project: {str(e)}")
                        return project_dir  # Still return the directory even if cursor launch fails
                
        except requests.exceptions.RequestException as e:
            st.error(f"Error creating project: {str(e)}")
            return None

def main():
    st.set_page_config(
        page_title="AI Creative Collaborator",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    collaborator = AICreativeCollaborator()
    collaborator.initialize_session()

    # Initialize project creation state if not exists
    if "project_creation_step" not in st.session_state:
        st.session_state.project_creation_step = 0
    
    # Sidebar
    with st.sidebar:
        st.title("Project Progress")
        progress_value = {
            "ideation": 0.33,
            "specification": 0.66,
            "implementation": 1.0
        }[st.session_state.current_phase]
        
        st.progress(progress_value)
        st.write(f"Current Phase: {st.session_state.current_phase.capitalize()}")
        
        if st.session_state.current_phase == "specification":
            # Display PRD in a collapsible container
            with st.expander("View PRD", expanded=True):
                st.json(st.session_state.project_spec)
            
            # Display project links if available
            if "projectLinks" in st.session_state.project_spec:
                st.subheader("Project Links")
                links = st.session_state.project_spec["projectLinks"]
                if "frontend" in links:
                    st.write(f"Frontend: [Open App]({links['frontend']})")
                if "backend" in links:
                    st.write(f"Backend: [API Endpoint]({links['backend']})")
                if "repository" in links:
                    st.write(f"Repository: {links['repository']}")
        
        if st.session_state.current_phase == "implementation":
            st.subheader("Project Links")
            if st.session_state.project_links:
                links = st.session_state.project_links
                st.write(f"Project Directory: {links.get('project_dir', 'N/A')}")
                st.write(f"Frontend: [Open App]({links.get('frontend', 'http://localhost:3000')})")
                st.write(f"Backend: [API Endpoint]({links.get('backend', 'http://localhost:3001')})")
                
                if st.button("Open in Browser"):
                    webbrowser.open(links.get('frontend', 'http://localhost:3000'))

    # Main content
    st.title("AI Creative Collaborator")
    
    if st.session_state.current_phase == "ideation":
        st.markdown("""
        ### Welcome to AI Creative Collaborator! 
        Share your project idea and let's develop it together. We'll:
        1. Discuss and refine your idea
        2. Generate a detailed PRD
        3. Create a Cursor project for implementation
        """)
        st.info("💡 Start by sharing your project idea. Mistral will ask clarifying questions to help refine it.")

    # Chat interface
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            if message["role"] != "system":  # Don't display system messages
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        if prompt := st.chat_input("Share your thoughts..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Get AI response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = collaborator.chat_with_ai(st.session_state.messages)
                    if response:
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        st.markdown(response)

    # Action buttons
    action_container = st.container()
    with action_container:
        col1, col2, col3 = st.columns(3)
        
        if st.session_state.current_phase == "ideation":
            # Only enable PRD button after some conversation
            button_disabled = len([m for m in st.session_state.messages if m["role"] == "user"]) < 3
            
            if col1.button("Generate PRD", type="primary", disabled=button_disabled):
                with st.spinner("Generating PRD..."):
                    spec = collaborator.generate_prd(st.session_state.messages)
                    if spec:
                        st.session_state.project_spec = spec
                        st.session_state.current_phase = "specification"
                        
                        # Add a message showing the PRD was generated
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": "✅ PRD successfully generated! You can view it in the sidebar. Click \"Setup Cursor Project\" to create a new implementation project."
                        })
                        
                        st.rerun()
            
            if button_disabled:
                col1.caption("Continue the conversation to enable PRD generation")

        elif st.session_state.current_phase == "specification":
            # Handle the project creation flow using session state
            if st.session_state.project_creation_step == 0:
                if col1.button("Setup Cursor Project", type="primary"):
                    st.session_state.project_creation_step = 1
                    st.rerun()
            elif st.session_state.project_creation_step == 1:
                # Show project name input form
                st.subheader("Create Project")
                project_name = st.text_input(
                    "Enter project name:", 
                    value=st.session_state.project_spec.get('title', '').lower().replace(' ', '_')
                )
                
                # Validate and proceed
                if not project_name:
                    st.warning("Please enter a project name to continue")
                else:
                    # Store name in session state
                    st.session_state.project_name = project_name
                    
                    if st.button("Create Project Now", type="primary"):
                        # Create project directory
                        with st.spinner("Creating project..."):
                            # Create project directory
                            spec = st.session_state.project_spec
                            # Update project links with port 3000
                            if "projectLinks" not in spec:
                                spec["projectLinks"] = {}
                            
                            spec["projectLinks"]["frontend"] = "http://localhost:3000"
                            spec["projectLinks"]["backend"] = "http://localhost:3001"
                            
                            # Call backend to get base project structure
                            try:
                                response = requests.post(
                                    f"{collaborator.api_url}/create-project",
                                    json=spec,
                                    timeout=collaborator.PROJECT_TIMEOUT
                                )
                                response.raise_for_status()
                                result = response.json()
                                temp_project_dir = result["project_dir"]
                                
                                # Create new project with user-defined name
                                new_project_dir = Path(os.path.expanduser("~")) / "Documents" / "cursor_projects" / project_name
                                
                                # Create parent directories if they don't exist
                                new_project_dir.parent.mkdir(parents=True, exist_ok=True)
                                
                                # If directory exists, remove it to avoid conflicts
                                if new_project_dir.exists():
                                    shutil.rmtree(new_project_dir)
                                    
                                new_project_dir.mkdir(exist_ok=True)
                                
                                # Copy files from project_dir to new_project_dir
                                for item in Path(temp_project_dir).glob('*'):
                                    if item.is_file():
                                        shutil.copy2(item, new_project_dir)
                                    elif item.is_dir():
                                        shutil.copytree(item, new_project_dir / item.name)
                                
                                # Create the IMPLEMENT_PRD.txt with the FULL PRD content
                                prd_content = f"""# {spec['title']} - PRD

## Please implement this PRD in a new project
Start a development server on port 3000.

## Project Overview
{spec['description']}

## Features
"""
                                # Add features
                                for feature in spec['features']:
                                    prd_content += f"- {feature['name']} ({feature['priority']}): {feature['description']}\n"
                                
                                prd_content += "\n## Technologies\n"
                                for tech in spec['technologies']:
                                    prd_content += f"- {tech['name']}: {tech['purpose']}\n"
                                
                                prd_content += f"\n## Architecture\nType: {spec['architecture']['type']}\n\nComponents:\n"
                                for comp in spec['architecture']['components']:
                                    prd_content += f"- {comp['name']}: {comp['purpose']}\n"
                                    prd_content += f"  Interactions: {', '.join(comp['interactions'])}\n"
                                
                                prd_content += "\n## Implementation Plan\n"
                                for i, phase in enumerate(spec['implementationPlan']):
                                    prd_content += f"### Phase {i+1}: {phase['phase']} ({phase['duration']})\n"
                                    for task in phase['tasks']:
                                        prd_content += f"- {task['name']} ({task['duration']})\n"
                                
                                # Write the full PRD content to IMPLEMENT_PRD.txt
                                with open(new_project_dir / "IMPLEMENT_PRD.txt", "w") as f:
                                    f.write(prd_content)
                                
                                # Add a package.json with port 3000 configured
                                package_json = {
                                    "name": project_name,
                                    "version": "1.0.0",
                                    "description": spec["description"],
                                    "main": "index.js",
                                    "scripts": {
                                        "start": "node server.js",
                                        "dev": "nodemon server.js"
                                    },
                                    "dependencies": {},
                                    "devDependencies": {},
                                    "port": 3000
                                }
                                
                                with open(new_project_dir / "package.json", "w") as f:
                                    json.dump(package_json, f, indent=2)
                                
                                # Create a basic server file that uses port 3000
                                server_js = """const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 3000;

const server = http.createServer((req, res) => {
  res.writeHead(200, {'Content-Type': 'text/html'});
  res.end('<h1>Project Implementation Server</h1><p>This project is running on port 3000</p>');
});

server.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}/`);
});
"""
                                with open(new_project_dir / "server.js", "w") as f:
                                    f.write(server_js)
                                
                                # Close any existing Cursor instances
                                subprocess.run(["pkill", "-f", "Cursor"], stderr=subprocess.DEVNULL)
                                subprocess.run(["sleep", "1"])
                                
                                # Open in a NEW Cursor window with absolute path
                                subprocess.Popen([collaborator.cursor_path, "--new-window", str(new_project_dir.absolute())])
                                
                                # Store project links
                                st.session_state.project_links = {
                                    "project_dir": str(new_project_dir.absolute()),
                                    "frontend": "http://localhost:3000",
                                    "backend": "http://localhost:3001"
                                }
                                
                                # Update phase and show success
                                st.session_state.current_phase = "implementation"
                                st.session_state.project_creation_step = 0
                                
                                # Add message with links
                                link_message = f"""
✅ **Project successfully created!**

**Project Location:** {str(new_project_dir.absolute())}  
**Frontend URL (after implementation):** http://localhost:3000  
**Backend URL (after implementation):** http://localhost:3001  

The project is now open in a new Cursor window with complete PRD documentation.
- The project structure and instructions have been set up
- Start the server by running `npm run dev` (after implementation)
- Access your application at http://localhost:3000
"""
                                st.session_state.messages.append({
                                    "role": "assistant", 
                                    "content": link_message
                                })
                                
                                st.success(f"Project created at: {str(new_project_dir.absolute())}")
                                st.balloons()
                                
                            except Exception as e:
                                st.error(f"Error creating project: {str(e)}")
                                st.session_state.project_creation_step = 0
                            
                            st.rerun()
                    
                    # Add a back button
                    if st.button("Back", type="secondary"):
                        st.session_state.project_creation_step = 0
                        st.rerun()

        if col3.button("Reset Session", type="secondary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main() 