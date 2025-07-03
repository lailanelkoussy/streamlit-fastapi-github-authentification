# GitHub Repository Explorer

A full-stack application that allows users to authenticate with GitHub and explore their private repositories through a web interface. Built with FastAPI backend and Streamlit frontend.

## Features

- 🔐 GitHub OAuth authentication
- 📁 Browse private and public repositories
- 📄 View file contents directly in the browser
- 🔍 Navigate through repository directory structure
- 🌟 Display repository metadata (stars, language, privacy status)
- 📊 Repository overview with sortable data

## Architecture

- **Backend**: FastAPI with GitHub OAuth integration
- **Frontend**: Streamlit web application
- **Authentication**: GitHub OAuth 2.0 with `repo` scope for private repository access
- **API Integration**: GitHub REST API for repository and file operations

## Prerequisites

- Python 3.8+
- GitHub account
- GitHub OAuth App (instructions below)

## Setup Instructions

### 1. Create GitHub OAuth App

1. Go to GitHub Settings → Developer settings → OAuth Apps
2. Click "New OAuth App"
3. Fill in the application details:
   - **Application name**: Your app name
   - **Homepage URL**: `http://localhost:8501` (for development)
   - **Authorization callback URL**: `http://localhost:8000/auth/github/callback`
4. Note down your **Client ID** and **Client Secret**

### 2. Clone and Install Dependencies

```bash
git clone <your-repository-url>
cd github-repository-explorer
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the root directory:

```bash
# Development environment
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_REDIRECT_URI=http://localhost:8000/auth/github/callback
FRONTEND_URL=http://localhost:8501
BACKEND_URL=http://localhost:8000
```

### 4. Run the Application

**Terminal 1 - Start FastAPI Backend:**
```bash
uvicorn fastapi_app:app --reload --port 8000
```

**Terminal 2 - Start Streamlit Frontend:**
```bash
streamlit run streamlit_app.py --server.port 8501
```

### 5. Access the Application

Open your browser and navigate to `http://localhost:8501`

## Required Dependencies

Create a `requirements.txt` file:

```txt
fastapi==0.104.1
uvicorn==0.24.0
streamlit==1.28.1
httpx==0.25.0
python-dotenv==1.0.0
pandas==2.1.3
requests==2.31.0
```

## File Structure

```
github-repository-explorer/
├── fastapi_app.py                 # FastAPI backend
├── streamlit_app.py        # Streamlit frontend
├── requirements.txt        # Python dependencies
├── .env                   # Environment variables (create this)
├── .env.example          # Example environment file
└── README.md             # This file
```

## API Endpoints

### Authentication
- `GET /auth/github` - Initiate GitHub OAuth flow
- `GET /auth/github/callback` - Handle OAuth callback

### User Operations
- `GET /user/{user_id}/info` - Get authenticated user information
- `GET /user/{user_id}/repos` - Get user's repositories (public and private)
- `GET /user/{user_id}/repo/{owner}/{repo}/contents` - Get repository contents
- `GET /user/{user_id}/repo/{owner}/{repo}/file` - Get specific file content

## GitHub OAuth Scopes

This application requests the following scopes:
- `repo` - Full access to repositories (required for private repos)
- `user` - Access to user profile information

## Production Deployment

### Environment Variables for Production

Create a `.env.prod` file:

```bash
# Production environment
GITHUB_CLIENT_ID=your_prod_github_client_id
GITHUB_CLIENT_SECRET=your_prod_github_client_secret
GITHUB_REDIRECT_URI=https://api.yourdomain.com/auth/github/callback
FRONTEND_URL=https://yourdomain.com
BACKEND_URL=https://api.yourdomain.com
```

### GitHub OAuth App Configuration for Production

Update your GitHub OAuth App settings:
- **Homepage URL**: `https://yourdomain.com`
- **Authorization callback URL**: `https://api.yourdomain.com/auth/github/callback`

### Deployment Options

#### Option 1: Single Domain
- Frontend: `https://myapp.com`
- Backend API: `https://myapp.com/api`
- Callback: `https://myapp.com/api/auth/github/callback`

#### Option 2: Separate Subdomains
- Frontend: `https://app.mycompany.com`
- Backend API: `https://api.mycompany.com`
- Callback: `https://api.mycompany.com/auth/github/callback`

#### Option 3: Microservices
- Frontend: `https://frontend.myapp.com`
- Auth Service: `https://auth.myapp.com`
- Callback: `https://auth.myapp.com/auth/github/callback`

### Cloud Platform Deployment

#### Heroku
```bash
# Set environment variables
heroku config:set GITHUB_CLIENT_ID=your_client_id
heroku config:set GITHUB_CLIENT_SECRET=your_client_secret
heroku config:set GITHUB_REDIRECT_URI=https://yourapp.herokuapp.com/auth/github/callback
heroku config:set FRONTEND_URL=https://yourapp.herokuapp.com
```

#### Docker
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV GITHUB_REDIRECT_URI=https://api.yourdomain.com/auth/github/callback
ENV FRONTEND_URL=https://yourdomain.com

CMD ["uvicorn", "fastapi_app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Security Considerations

### Development vs Production

**Development:**
- HTTP is acceptable for localhost
- In-memory token storage is fine for testing
- Single GitHub OAuth app can be used

**Production:**
- ✅ Always use HTTPS
- ✅ Implement secure token storage (database with encryption)
- ✅ Use separate GitHub OAuth apps for different environments
- ✅ Implement proper session management
- ✅ Add rate limiting
- ✅ Validate CORS origins strictly
- ✅ Use environment variables for all sensitive data

### Important Security Notes

1. **Token Storage**: This demo uses in-memory storage. For production, use:
   - Encrypted database storage
   - Redis with encryption
   - Cloud-based secret management (AWS Secrets Manager, etc.)

2. **Session Management**: Implement proper session handling with:
   - Session timeouts
   - Secure session cookies
   - Session invalidation on logout

3. **Rate Limiting**: GitHub API has rate limits:
   - 5,000 requests per hour for authenticated requests
   - Implement caching for frequently accessed data
   - Add client-side rate limiting

4. **CORS Configuration**: Restrict CORS to your actual domains
5. **Error Handling**: Don't expose sensitive information in error messages
6. **Logging**: Implement proper logging without logging sensitive data

## Troubleshooting

### Common Issues

1. **OAuth Callback URL Mismatch**
   - Ensure GitHub OAuth app callback URL matches your `GITHUB_REDIRECT_URI`
   - Check for trailing slashes and http vs https

2. **CORS Issues**
   - Verify `FRONTEND_URL` in backend CORS configuration
   - Check browser console for CORS errors

3. **Token Expiration**
   - GitHub tokens don't expire by default, but can be revoked
   - Implement token refresh logic for production

4. **Rate Limiting**
   - GitHub API limits: 5,000 requests/hour
   - Implement exponential backoff for failed requests

5. **Private Repository Access**
   - Ensure `repo` scope is requested during OAuth
   - Check that user has access to the repository

### Debug Mode

Enable debug logging by adding to your FastAPI app:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## API Rate Limits

- **GitHub API**: 5,000 requests per hour (authenticated)
- **Recommendations**:
  - Cache repository lists
  - Implement request throttling
  - Use conditional requests when possible

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review GitHub OAuth documentation
3. Check FastAPI and Streamlit documentation
4. Open an issue in this repository
