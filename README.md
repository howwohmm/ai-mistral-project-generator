# AI Project Generator with Mistral

A collaborative AI assistant that helps you refine project ideas and generate structured PRDs (Product Requirement Documents) using the Mistral AI model.

## Features

- **Collaborative Ideation**: Have a structured conversation with AI to refine your project idea
- **PRD Generation**: Create detailed PRDs with features, technologies, and implementation plans
- **Project Creation**: Generate complete project structures with implementation guides
- **Cursor Integration**: Open projects directly in the Cursor editor

## Setup

### Requirements

- Python 3.8+
- Mistral API Key

### Installation

1. Clone this repository:
```bash
git clone https://github.com/howwohmm/ai-mistral-project-generator.git
cd ai-mistral-project-generator
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your Mistral API key:
```
MISTRAL_API_KEY=your_mistral_api_key
MODEL_NAME=mistral-large-latest
```

### Running Locally

1. Start the backend server:
```bash
cd src/backend
python main.py
```

2. Start the Streamlit frontend (in a new terminal):
```bash
cd src/frontend
streamlit run app.py --server.port 8502
```

3. Open your browser to [http://localhost:8502](http://localhost:8502)

## Deployment

This project is configured for deployment on Vercel.

## License

MIT

## Credits

Built with Mistral AI and Streamlit.

## Project Structure

```
ai-creative-collaborator/
├── src/
│   ├── backend/
│   │   └── main.py           # FastAPI backend with Mistral integration
│   └── frontend/
│       └── app.py            # Streamlit frontend
├── docs/                     # Documentation files
├── generated_projects/       # Generated project directories
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Support

For support, please:
1. Check the documentation in the docs/ directory
2. Open an issue in the GitHub repository
3. Contact the maintainers

## Roadmap

- [ ] Add support for multiple project templates
- [ ] Implement collaborative features
- [ ] Add version control integration
- [ ] Enhance code generation capabilities
- [ ] Add support for additional IDEs 