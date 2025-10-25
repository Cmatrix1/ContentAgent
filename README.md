# Content Agent

A Django-based content management and search application with Google Custom Search API integration.

## Features

- **Search**: Google Custom Search API integration with automatic API key rotation
- **Accounts**: User account management
- **Publication**: Content publication management
- **REST API**: Full REST API with Django REST Framework
- **PostgreSQL**: Production-ready PostgreSQL database
- **Docker**: Containerized deployment with Docker Compose

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL (if running locally without Docker)

## Quick Start with Docker

1. Clone the repository:
```bash
git clone <repository-url>
cd ContentAgent
```

2. Create your environment file:
```bash
cp .example.env .env
```

3. Update the `.env` file with your configuration (especially the Google API credentials)

4. Build and start the application:
```bash
make dev
# or
docker-compose up --build
```

The application will automatically:
- Wait for PostgreSQL to be ready
- Run database migrations
- Collect static files
- Start the server

5. Create a superuser (in a new terminal):
```bash
make createsuperuser
# or
docker-compose exec web python manage.py createsuperuser
```

6. Access the application:
- API: http://localhost:8000
- Admin Panel: http://localhost:8000/admin

## Local Development Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file from `.example.env` and configure it

4. Run migrations:
```bash
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

## Environment Variables

See `.example.env` for all available environment variables. Key variables include:

- `SECRET_KEY`: Django secret key (change in production!)
- `DEBUG`: Debug mode (set to False in production)
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`: PostgreSQL configuration
- `GOOGLE_API_KEYS`: Comma-separated Google API keys for search
- `GOOGLE_SEARCH_ENGINE_ID`: Google Custom Search Engine ID

## Project Structure

```
ContentAgent/
├── apps/
│   ├── accounts/       # User account management
│   ├── publication/    # Content publication
│   └── search/         # Google search integration
├── config/             # Django configuration
├── logs/               # Application logs
├── docker-compose.yml  # Docker Compose configuration
├── Dockerfile          # Docker image definition
└── manage.py           # Django management script
```

## API Endpoints

- `/api/search/`: Search endpoints
- `/admin/`: Django admin panel

## Logging

Logs are stored in the `logs/` directory:
- `django.log`: General application logs
- `django_error.log`: Error logs

## Production Deployment

1. Set `DEBUG=False` in your `.env` file
2. Generate a strong `SECRET_KEY`
3. Update `ALLOWED_HOSTS` with your domain
4. Configure your production database settings
5. Run with Docker Compose or deploy to your preferred platform

