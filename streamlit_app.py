import streamlit as st
import requests
import pandas as pd
from urllib.parse import parse_qs, urlparse

# Configure the page
st.set_page_config(page_title="GitHub Repository Explorer", layout="wide")

# Backend URL
BACKEND_URL = "http://localhost:8000"


def init_session_state():
    """Initialize session state variables"""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'repos' not in st.session_state:
        st.session_state.repos = None


def authenticate_github():
    """Initiate GitHub authentication"""
    try:
        response = requests.get(f"{BACKEND_URL}/auth/github")
        if response.status_code == 200:
            auth_data = response.json()
            st.session_state.auth_url = auth_data["auth_url"]
            st.markdown(f"[🔐 Authenticate with GitHub]({auth_data['auth_url']})")
            st.info("Click the link above to authenticate with GitHub. You'll be redirected back here.")
        else:
            st.error("Failed to initiate GitHub authentication")
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")


def get_user_info(user_id):
    """Get authenticated user information"""
    try:
        response = requests.get(f"{BACKEND_URL}/user/{user_id}/info")
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Failed to get user information")
            return None
    except Exception as e:
        st.error(f"Error getting user info: {e}")
        return None


def get_user_repos(user_id):
    """Get user's repositories"""
    try:
        response = requests.get(f"{BACKEND_URL}/user/{user_id}/repos")
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Failed to fetch repositories")
            return None
    except Exception as e:
        st.error(f"Error fetching repositories: {e}")
        return None


def get_repo_contents(user_id, owner, repo, path=""):
    """Get repository contents"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/user/{user_id}/repo/{owner}/{repo}/contents",
            params={"path": path}
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch contents: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error fetching contents: {e}")
        return None


def get_file_content(user_id, owner, repo, path):
    """Get file content"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/user/{user_id}/repo/{owner}/{repo}/file",
            params={"path": path}
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch file: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error fetching file: {e}")
        return None


def main():
    init_session_state()

    st.title("🐙 GitHub Repository Explorer")

    # Check for user_id in URL parameters (after OAuth redirect)
    query_params = st.query_params
    if 'user_id' in query_params and not st.session_state.user_id:
        st.session_state.user_id = int(query_params['user_id'])
        st.rerun()

    # Authentication section
    if not st.session_state.user_id:
        st.header("Authentication Required")
        st.write("Please authenticate with GitHub to access your repositories.")
        authenticate_github()
        return

    # Get user info if not already loaded
    if not st.session_state.user_info:
        st.session_state.user_info = get_user_info(st.session_state.user_id)
        if not st.session_state.user_info:
            st.session_state.user_id = None
            st.rerun()

    # Display user info
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.session_state.user_info.get('avatar_url'):
            st.image(st.session_state.user_info['avatar_url'], width=80)
    with col2:
        st.write(f"**Welcome, {st.session_state.user_info.get('name', st.session_state.user_info.get('login'))}!**")
        st.write(f"GitHub: @{st.session_state.user_info.get('login')}")
        if st.button("🔓 Logout"):
            st.session_state.user_id = None
            st.session_state.user_info = None
            st.session_state.repos = None
            st.rerun()

    st.divider()

    # Repository section
    st.header("📁 Your Repositories")

    if st.button("🔄 Refresh Repositories"):
        st.session_state.repos = None

    if not st.session_state.repos:
        with st.spinner("Loading repositories..."):
            st.session_state.repos = get_user_repos(st.session_state.user_id)

    if st.session_state.repos:
        # Create a DataFrame for better display
        repo_data = []
        for repo in st.session_state.repos:
            repo_data.append({
                'Name': repo['name'],
                'Private': '🔒' if repo['private'] else '🔓',
                'Language': repo.get('language', 'N/A'),
                'Stars': repo.get('stargazers_count', 0),
                'Updated': repo.get('updated_at', '').split('T')[0] if repo.get('updated_at') else 'N/A',
                'Full Name': repo['full_name']
            })

        df = pd.DataFrame(repo_data)

        # Repository selector
        selected_repo = st.selectbox(
            "Select a repository to explore:",
            options=df['Full Name'].tolist(),
            format_func=lambda x: f"{x} {'🔒' if df[df['Full Name'] == x]['Private'].iloc[0] == '🔒' else '🔓'}"
        )

        if selected_repo:
            owner, repo_name = selected_repo.split('/')

            # Repository explorer
            st.subheader(f"📂 Exploring: {selected_repo}")

            # Path navigation
            if 'current_path' not in st.session_state:
                st.session_state.current_path = ""

            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**Current path:** `/{st.session_state.current_path}`")
            with col2:
                if st.button("🏠 Go to Root"):
                    st.session_state.current_path = ""
                    st.rerun()

            # Get contents
            contents = get_repo_contents(
                st.session_state.user_id,
                owner,
                repo_name,
                st.session_state.current_path
            )

            if contents:
                # Display contents
                for item in contents:
                    col1, col2, col3 = st.columns([1, 6, 1])

                    with col1:
                        icon = "📁" if item['type'] == 'dir' else "📄"
                        st.write(icon)

                    with col2:
                        st.write(f"**{item['name']}**")

                    with col3:
                        if item['type'] == 'dir':
                            if st.button(f"Open", key=f"open_{item['path']}"):
                                st.session_state.current_path = item['path']
                                st.rerun()
                        else:
                            if st.button(f"View", key=f"view_{item['path']}"):
                                file_content = get_file_content(
                                    st.session_state.user_id,
                                    owner,
                                    repo_name,
                                    item['path']
                                )
                                if file_content:
                                    st.subheader(f"📄 {file_content['name']}")
                                    st.code(file_content['content'], language=None)

                # Back button for navigation
                if st.session_state.current_path:
                    if st.button("⬅️ Back"):
                        path_parts = st.session_state.current_path.split('/')
                        if len(path_parts) > 1:
                            st.session_state.current_path = '/'.join(path_parts[:-1])
                        else:
                            st.session_state.current_path = ""
                        st.rerun()

    # Display repository table
    if st.session_state.repos:
        st.subheader("📊 Repository Overview")
        st.dataframe(df.drop('Full Name', axis=1), use_container_width=True)


if __name__ == "__main__":
    main()