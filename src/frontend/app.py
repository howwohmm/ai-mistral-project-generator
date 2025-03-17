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
                
                # Send request to backend API - make sure we're using the correct endpoint
                # The API URL already includes /api, so we don't need to add it again
                endpoint = "/chat"
                
                # Debug the full URL being called
                full_url = f"{self.api_url}{endpoint}"
                print(f"Calling API at: {full_url}")
                st.sidebar.info(f"Calling: {full_url}")
                
                response = requests.post(
                    full_url,
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