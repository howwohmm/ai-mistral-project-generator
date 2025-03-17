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
                
                endpoint = "/create-project"
                full_url = f"{self.api_url}{endpoint}"
                print(f"Calling API at: {full_url}")
                
                response = requests.post(
                    full_url,
                    json=spec,
                    timeout=self.PROJECT_TIMEOUT
                )
                response.raise_for_status()
                result = response.json()
                project_dir = result["project_dir"]