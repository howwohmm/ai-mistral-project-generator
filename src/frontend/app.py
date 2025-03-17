    def generate_prd(self, messages):
        try:
            with st.spinner("Generating PRD with Mistral... This may take a few minutes."):
                # We don't need to add a system message - backend will handle that
                endpoint = "/generate-prd"
                full_url = f"{self.api_url}{endpoint}"
                print(f"Calling API at: {full_url}")
                
                response = requests.post(
                    full_url,
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