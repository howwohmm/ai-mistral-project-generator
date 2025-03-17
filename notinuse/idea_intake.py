import os
import json
import openai
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
from rich import print as rprint
from rich.progress import Progress
import time

# Initialize Rich console for better formatting
console = Console()

# Load environment variables from .env file
load_dotenv()

# Get API key from environment or set it directly here
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")

def initialize_openai():
    """Initialize OpenAI client with API key"""
    if not OPENAI_API_KEY:
        api_key = Prompt.ask("Enter your OpenAI API key")
        os.environ["OPENAI_API_KEY"] = api_key
    
    return openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def welcome_message():
    """Display a welcome message"""
    welcome_text = """
    # CURSOR AI AGENT - IDEA INTAKE

    I'm an advanced AI architect specializing in breaking down rough ideas into structured specifications.
    My goal is to extract 80% clarity before generating a prototype plan.
    I'll ask you targeted questions in a structured manner to refine your idea.
    
    Type 'exit' at any prompt to quit.
    """
    console.print(Panel(Markdown(welcome_text), style="bold blue"))

def get_core_idea():
    """Step 1: Understanding the Core Idea"""
    console.print("\n[bold]🔍 Step 1: Understanding the Core Idea[/bold]")
    
    # Get initial idea
    console.print("\n[bold]📝 What is your rough idea?[/bold]")
    console.print("Describe it in as much or as little detail as you have:")
    idea = Prompt.ask("\nYour idea", console=console)
    
    if idea.lower() == 'exit':
        console.print("\nGoodbye!", style="bold red")
        exit()
    
    # Get problem and target audience
    console.print("\n[bold]🔍 What problem does this solve? Who is the target audience?[/bold]")
    problem_audience = Prompt.ask("\nProblem & audience", console=console)
    
    if problem_audience.lower() == 'exit':
        console.print("\nGoodbye!", style="bold red")
        exit()
    
    # Get inspiration
    console.print("\n[bold]💡 Do you have an existing reference or inspiration for this?[/bold]")
    console.print("(e.g., a similar app, product, or service)")
    inspiration = Prompt.ask("\nInspiration", default="None", console=console)
    
    if inspiration.lower() == 'exit':
        console.print("\nGoodbye!", style="bold red")
        exit()
    
    return {
        "idea": idea,
        "problem_audience": problem_audience,
        "inspiration": inspiration
    }

def scope_project():
    """Step 2: Scoping the Project"""
    console.print("\n[bold]🔎 Step 2: Scoping the Project[/bold]")
    
    # Get project type
    project_types = {
        "1": "Web App",
        "2": "Mobile App",
        "3": "API-based Service",
        "4": "AI-powered Tool",
        "5": "CLI Tool",
        "6": "Other"
    }
    
    console.print("\n[bold]📌 What kind of project is this?[/bold]")
    for key, value in project_types.items():
        console.print(f"{key}. {value}")
    
    choice = Prompt.ask("\nProject type", choices=list(project_types.keys()) + ["exit"], console=console)
    
    if choice.lower() == 'exit':
        console.print("\nGoodbye!", style="bold red")
        exit()
    
    project_type = project_types[choice]
    if choice == "6":
        project_type = Prompt.ask("Please specify the project type", console=console)
    
    # Get key actions
    console.print("\n[bold]⚙️ What are the key actions a user should be able to take?[/bold]")
    console.print("(Example: Sign up, upload files, generate reports, etc.)")
    actions = Prompt.ask("\nKey actions", console=console)
    
    if actions.lower() == 'exit':
        console.print("\nGoodbye!", style="bold red")
        exit()
    
    # Get expected outcome
    console.print("\n[bold]🎯 What is the expected outcome or end-goal of using this?[/bold]")
    console.print("(What happens when the user completes a flow?)")
    outcome = Prompt.ask("\nExpected outcome", console=console)
    
    if outcome.lower() == 'exit':
        console.print("\nGoodbye!", style="bold red")
        exit()
    
    return {
        "project_type": project_type,
        "key_actions": actions,
        "expected_outcome": outcome
    }

def technical_scope():
    """Step 3: Technical Scope & Feasibility"""
    console.print("\n[bold]🔧 Step 3: Technical Scope & Feasibility[/bold]")
    
    # Get tech stack preference
    console.print("\n[bold]🛠 Do you have a preferred tech stack, or should I suggest one?[/bold]")
    has_preference = Confirm.ask("Do you have a preferred tech stack?", console=console)
    
    if has_preference:
        tech_stack = Prompt.ask("Please specify your preferred tech stack", console=console)
    else:
        tech_stack = "To be suggested based on project requirements"
    
    if tech_stack.lower() == 'exit':
        console.print("\nGoodbye!", style="bold red")
        exit()
    
    # Get external integrations
    console.print("\n[bold]📡 Does this require external integrations?[/bold]")
    console.print("(e.g., OpenAI, databases, APIs)")
    integrations = Prompt.ask("\nExternal integrations", default="None", console=console)
    
    if integrations.lower() == 'exit':
        console.print("\nGoodbye!", style="bold red")
        exit()
    
    # Get connectivity requirements
    console.print("\n[bold]🔗 Should this support offline mode, real-time updates, or both?[/bold]")
    connectivity = Prompt.ask("\nConnectivity", choices=["Offline only", "Online only", "Both", "Not applicable"], console=console)
    
    if connectivity.lower() == 'exit':
        console.print("\nGoodbye!", style="bold red")
        exit()
    
    # Get MVP expectations
    console.print("\n[bold]🚀 What is the minimum viable version (MVP) you'd like to see?[/bold]")
    console.print("(Example: \"A working prototype with login, file upload, and AI processing.\")")
    mvp = Prompt.ask("\nMVP expectations", console=console)
    
    if mvp.lower() == 'exit':
        console.print("\nGoodbye!", style="bold red")
        exit()
    
    return {
        "tech_stack": tech_stack,
        "external_integrations": integrations,
        "connectivity": connectivity,
        "mvp_expectations": mvp
    }

def ui_experience():
    """Step 4: UI & User Experience"""
    console.print("\n[bold]🎨 Step 4: UI & User Experience[/bold]")
    
    # Check if UI is needed
    console.print("\n[bold]📱 Should this have a UI, or will it be a backend-only tool?[/bold]")
    has_ui = Confirm.ask("Should this project have a UI?", console=console)
    
    if not has_ui:
        return {
            "has_ui": False,
            "key_screens": "Backend only",
            "dark_mode": False
        }
    
    # Get key screens
    console.print("\n[bold]🔲 Describe the key screens or interactions you imagine.[/bold]")
    console.print("(Example: Home screen → Input page → Results page.)")
    screens = Prompt.ask("\nKey screens/interactions", console=console)
    
    if screens.lower() == 'exit':
        console.print("\nGoodbye!", style="bold red")
        exit()
    
    # Dark mode preference
    console.print("\n[bold]🌓 Do you want a dark mode/light mode toggle?[/bold]")
    dark_mode = Confirm.ask("Include dark mode/light mode toggle?", console=console)
    
    return {
        "has_ui": True,
        "key_screens": screens,
        "dark_mode": dark_mode
    }

def ai_details():
    """Step 5: AI-Specific Details (If Applicable)"""
    console.print("\n[bold]📝 Step 5: AI-Specific Details (If Applicable)[/bold]")
    
    # Check if AI is involved
    console.print("\n[bold]🤖 Does this project involve AI? If yes, what role does it play?[/bold]")
    console.print("(Example: AI-generated content, smart recommendations, automation.)")
    
    ai_involved = Confirm.ask("Does this project involve AI?", console=console)
    
    if not ai_involved:
        return {
            "ai_involved": False,
            "ai_role": "None",
            "ai_learning": "N/A",
            "ai_processing": "N/A",
            "ai_behavior": "N/A"
        }
    
    ai_role = Prompt.ask("What role does AI play in this project?", console=console)
    
    if ai_role.lower() == 'exit':
        console.print("\nGoodbye!", style="bold red")
        exit()
    
    # AI learning
    console.print("\n[bold]📊 Does AI need to learn from user data over time?[/bold]")
    ai_learning = Confirm.ask("Should AI learn from user data?", console=console)
    ai_learning_details = "No adaptive learning" if not ai_learning else Prompt.ask("Explain how it should adapt", console=console)
    
    # AI processing
    console.print("\n[bold]⏳ Should the AI process information instantly, or can it take time?[/bold]")
    ai_processing = Prompt.ask("AI processing type", choices=["Real-time", "Batch processing", "Both"], console=console)
    
    # AI behavior
    console.print("\n[bold]📚 Should the AI summarize, generate, or predict information?[/bold]")
    ai_behavior = Prompt.ask("AI behavior", choices=["Summarize", "Generate", "Predict", "Multiple", "Other"], console=console)
    
    if ai_behavior == "Multiple" or ai_behavior == "Other":
        ai_behavior = Prompt.ask("Please specify AI behavior in detail", console=console)
    
    return {
        "ai_involved": True,
        "ai_role": ai_role,
        "ai_learning": ai_learning_details,
        "ai_processing": ai_processing,
        "ai_behavior": ai_behavior
    }

def final_refinements():
    """Step 6: Final Refinements & Missing Info"""
    console.print("\n[bold]📌 Step 6: Final Refinements & Missing Info[/bold]")
    
    # Get constraints
    console.print("\n[bold]🔄 Are there any constraints I should be aware of?[/bold]")
    console.print("(e.g., budget, computing power, legal concerns)")
    constraints = Prompt.ask("\nConstraints", default="None", console=console)
    
    if constraints.lower() == 'exit':
        console.print("\nGoodbye!", style="bold red")
        exit()
    
    # Get additional info
    console.print("\n[bold]💬 Is there anything I missed that you think is important?[/bold]")
    additional_info = Prompt.ask("\nAdditional information", default="None", console=console)
    
    if additional_info.lower() == 'exit':
        console.print("\nGoodbye!", style="bold red")
        exit()
    
    return {
        "constraints": constraints,
        "additional_info": additional_info
    }

def process_with_chatgpt(client, project_data):
    """Process the gathered data with ChatGPT to get structured specifications"""
    console.print("\n[bold]Processing your idea with ChatGPT...[/bold]")
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Generating specification...", total=100)
        
        while not progress.finished:
            progress.update(task, advance=0.5)
            time.sleep(0.01)
    
    try:
        # Craft a detailed prompt based on all collected information
        system_prompt = """
        You are an advanced AI architect specializing in breaking down rough ideas into structured specifications.
        Convert the provided project information into a detailed technical specification.
        Your response MUST be a valid, parseable JSON object.
        """
        
        user_prompt = f"""
        I've collected detailed information about a project idea. Please convert this into a comprehensive 
        specification that can be used for implementation:
        
        # Core Idea
        - Idea: {project_data['core_idea']['idea']}
        - Problem & Target Audience: {project_data['core_idea']['problem_audience']}
        - Inspiration: {project_data['core_idea']['inspiration']}
        
        # Project Scope
        - Project Type: {project_data['project_scope']['project_type']}
        - Key User Actions: {project_data['project_scope']['key_actions']}
        - Expected Outcome: {project_data['project_scope']['expected_outcome']}
        
        # Technical Requirements
        - Tech Stack: {project_data['technical_scope']['tech_stack']}
        - External Integrations: {project_data['technical_scope']['external_integrations']}
        - Connectivity: {project_data['technical_scope']['connectivity']}
        - MVP Expectations: {project_data['technical_scope']['mvp_expectations']}
        
        # UI & UX
        - Has UI: {project_data['ui_experience']['has_ui']}
        - Key Screens: {project_data['ui_experience']['key_screens']}
        - Dark Mode Support: {project_data['ui_experience']['dark_mode']}
        
        # AI Components
        - AI Involved: {project_data['ai_details']['ai_involved']}
        - AI Role: {project_data['ai_details']['ai_role']}
        - AI Learning: {project_data['ai_details']['ai_learning']}
        - AI Processing: {project_data['ai_details']['ai_processing']}
        - AI Behavior: {project_data['ai_details']['ai_behavior']}
        
        # Additional Information
        - Constraints: {project_data['refinements']['constraints']}
        - Additional Info: {project_data['refinements']['additional_info']}
        
        Generate a response as a JSON object with these fields:
        1. project_title: A catchy name for the project
        2. project_description: A brief description of what it does
        3. target_users: Who will use this application
        4. key_features: An array of main features (each with name and description)
        5. technical_stack: Recommended technologies to use (be specific with versions if possible)
        6. components: Main components or files needed
        7. data_model: Any data structures or models needed
        8. api_endpoints: For web/mobile apps, any API endpoints needed
        9. user_interface: Brief description of key UI elements
        10. ai_components: If applicable, AI models, training data, and implementation approach
        11. implementation_plan: Steps to build the MVP
        12. missing_info: What other information would be helpful to know
        
        Make sure your output is valid JSON that can be parsed.
        """
        
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        specification = json.loads(response.choices[0].message.content)
        return specification
    
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
        return {"error": str(e)}

def display_specification(specification):
    """Display the specification in a readable format"""
    if "error" in specification:
        console.print("\n[bold red]There was an error processing your idea:[/bold red]")
        console.print(specification["error"])
        return
    
    # Create a markdown representation of the specification
    spec_md = f"""
    # {specification.get('project_title', 'PROJECT SPECIFICATION')}

    ## Description
    {specification.get('project_description', 'N/A')}

    ## Target Users
    {specification.get('target_users', 'N/A')}

    ## Key Features
    """
    
    for feature in specification.get('key_features', []):
        spec_md += f"\n* **{feature.get('name')}**: {feature.get('description')}"
    
    spec_md += f"""
    
    ## Technical Stack
    {specification.get('technical_stack', 'N/A')}

    ## Components
    """
    
    for component in specification.get('components', []):
        spec_md += f"\n* {component}"
    
    if specification.get('ai_components'):
        spec_md += f"""
        
        ## AI Components
        {specification.get('ai_components', 'N/A')}
        """
    
    spec_md += f"""
    
    ## Implementation Plan
    """
    
    implementation_plan = specification.get('implementation_plan', [])
    if isinstance(implementation_plan, list):
        for i, step in enumerate(implementation_plan, 1):
            spec_md += f"\n{i}. {step}"
    else:
        spec_md += f"\n{implementation_plan}"
    
    spec_md += """
    
    ## Missing Information
    """
    
    for info in specification.get('missing_info', []):
        spec_md += f"\n* {info}"
    
    console.print(Panel(Markdown(spec_md), title="Project Specification", style="bold blue"))

def save_specification(specification):
    """Save the specification to a JSON file"""
    # Create specs directory if it doesn't exist
    os.makedirs("specs", exist_ok=True)
    
    filename = f"specs/{specification.get('project_title', 'project').lower().replace(' ', '_')}_spec.json"
    
    with open(filename, "w") as f:
        json.dump(specification, f, indent=2)
    
    console.print(f"\nSpecification saved to [bold green]{filename}[/bold green]")
    return filename

def main():
    # Initialize OpenAI client
    client = initialize_openai()
    
    # Show welcome message
    welcome_message()
    
    # Step 1: Core Idea
    core_idea = get_core_idea()
    
    # Step 2: Project Scope
    project_scope = scope_project()
    
    # Step 3: Technical Scope
    technical_scope_data = technical_scope()
    
    # Step 4: UI Experience
    ui_exp = ui_experience()
    
    # Step 5: AI Details
    ai_data = ai_details()
    
    # Step 6: Final Refinements
    refinements = final_refinements()
    
    # Consolidate all data
    project_data = {
        "core_idea": core_idea,
        "project_scope": project_scope,
        "technical_scope": technical_scope_data,
        "ui_experience": ui_exp,
        "ai_details": ai_data,
        "refinements": refinements
    }
    
    # Process with ChatGPT
    specification = process_with_chatgpt(client, project_data)
    
    # Display the structured specification
    display_specification(specification)
    
    # Save the specification
    spec_file = save_specification(specification)
    
    # Ask about next steps
    proceed = Prompt.ask(
        "\nWould you like to proceed to implementation with Cursor?",
        choices=["yes", "no"],
        default="yes"
    )
    
    if proceed.lower() == "yes":
        console.print("\n[bold green]Great![/bold green] We'll implement the Cursor integration next.")
        console.print(f"The specification file [bold]{spec_file}[/bold] will be used for implementation.")
    else:
        console.print("\nNo problem! You can refine your idea or try again later.")

if __name__ == "__main__":
    main() 