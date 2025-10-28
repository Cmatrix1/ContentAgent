# ContentAgent

A Django-based content management system with automated video downloading from Instagram, YouTube, and LinkedIn.

## 🚀 Features

- ✅ **Project Management**: Create and manage content projects
- ✅ **Google Search Integration**: Search for content using Google Custom Search API
- ✅ **Content Management**: Save and organize content from search results
- ✅ **Automated Video Downloads**: Background downloading of videos from multiple platforms
  - Instagram (via APIHUT.IN API)
  - YouTube (via APIHUT.IN API)
  - LinkedIn (via yt-dlp)
- ✅ **Download Status Tracking**: Real-time tracking of download progress
- ✅ **RESTful API**: Complete REST API for all operations
- ✅ **Background Tasks**: Celery-based task queue for asynchronous processing
- ✅ **Admin Interface**: Django admin for easy management

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL
- Redis (for Celery)
- yt-dlp (for LinkedIn videos)

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ContentAgent
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file:

```env
# Database
DB_NAME=contentagent
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Celery & Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Google Search API
GOOGLE_API_KEY=your-google-api-key
GOOGLE_SEARCH_ENGINE_ID=your-search-engine-id

# APIHUT.IN API
APIHUT_API_URL=https://apihut.in/api/download/videos
```

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Create Superuser

```bash
python manage.py createsuperuser
```

### 6. Start Services

#### Start Redis (Docker)
```bash
docker run -d -p 6379:6379 --name contentagent-redis redis:latest
```

#### Start Django Server
```bash
python manage.py runserver
```

#### Start Celery Worker (New Terminal)
```bash
# Windows
celery -A config worker --loglevel=info --pool=solo

# Linux/Mac
celery -A config worker --loglevel=info
```

## 📖 Quick Start

See [Quick Start Guide](docs/QUICKSTART.md) for a step-by-step tutorial.

## 📚 API Documentation

See [Content API Documentation](docs/CONTENT_API.md) for complete API reference.

## 🏗️ Architecture

```
┌─────────────┐
│   User/API  │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌──────────────┐
│   Django    │────▶│  PostgreSQL  │
│   Server    │     └──────────────┘
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌──────────────┐
│   Celery    │────▶│    Redis     │
│   Worker    │     └──────────────┘
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌──────────────┐
│  Video APIs │────▶│ Media Storage│
└─────────────┘     └──────────────┘
```

## 📁 Project Structure

```
ContentAgent/
├── apps/
│   ├── accounts/         # User management
│   ├── search/           # Search functionality
│   ├── content/          # Content management & video downloads
│   └── publication/      # Publishing features
├── config/
│   ├── settings.py       # Django settings
│   ├── urls.py           # Main URL configuration
│   ├── celery.py         # Celery configuration
│   └── wsgi.py           # WSGI configuration
├── docs/                 # Documentation
├── logs/                 # Application logs
├── media/                # User uploaded & downloaded files
├── requirements.txt      # Python dependencies
└── manage.py            # Django management script
```

## 🔌 API Endpoints

### Projects
- `POST /api/projects/create/` - Create a new project
- `GET /api/projects/{id}/` - Get project details

### Search
- `POST /api/projects/{id}/search/` - Search for content
- `GET /api/projects/{id}/search-results/` - Get search results

### Content Management
- `POST /api/projects/{id}/contents/create/` - Save content & trigger download
- `GET /api/projects/{id}/contents/` - List project contents
- `GET /api/projects/{id}/contents/{id}/` - Get content details
- `DELETE /api/projects/{id}/contents/{id}/` - Delete content

### Download Status
- `GET /api/projects/{id}/contents/{id}/download-status/` - Get download status
- `GET /api/download-tasks/{id}/` - Get download task details

## 🎯 Usage Example

### 1. Create a Project
```bash
curl -X POST http://localhost:8000/api/projects/create/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "My Project", "type": "video"}'
```

### 2. Search for Content
```bash
curl -X POST http://localhost:8000/api/projects/{project_id}/search/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "AI trends", "top_results_count": 10}'
```

### 3. Save Video Content
```bash
curl -X POST http://localhost:8000/api/projects/{project_id}/contents/create/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "AI Video",
    "source_url": "https://www.instagram.com/reel/...",
    "content_type": "video",
    "platform": "instagram"
  }'
```

### 4. Check Download Status
```bash
curl -X GET http://localhost:8000/api/projects/{project_id}/contents/{content_id}/download-status/ \
  -H "Authorization: Token YOUR_TOKEN"
```

## 🧪 Development

### Running Tests
```bash
python manage.py test
```

### Code Style
```bash
flake8 apps/
black apps/
```

### Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

## 🐳 Docker Support

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📊 Monitoring

### Celery Monitoring with Flower (Optional)

```bash
# Install Flower
pip install flower

# Start Flower
celery -A config flower
```

Access at: `http://localhost:5555`

## 🔒 Security

- JWT/Token authentication required for all API endpoints
- CSRF protection enabled
- Secure session cookies
- CORS configuration for frontend integration
- SQL injection protection via Django ORM

## 🚀 Production Deployment

### Environment Variables
Set appropriate production values for:
- `DEBUG=False`
- `SECRET_KEY` (strong random key)
- `ALLOWED_HOSTS`
- Database credentials
- Redis URL
- API keys

### Static Files
```bash
python manage.py collectstatic
```

### WSGI Server
Use Gunicorn or uWSGI for production:
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Django & Django REST Framework
- Celery for background tasks
- yt-dlp for video downloading
- APIHUT.IN for video API services

## 📧 Support

For issues and questions:
- Open an issue on GitHub
- Check the documentation in `/docs`
- Review logs in `/logs`

## 🗺️ Roadmap

- [ ] Video transcoding support
- [ ] Multi-format downloads
- [ ] Webhook notifications
- [ ] Advanced search filters
- [ ] Content analytics
- [ ] Batch operations
- [ ] Export functionality
- [ ] API rate limiting improvements

---

Made with ❤️ by the ContentAgent Team
