# Playwright Service

A web scraping service built with **FastAPI**, **PostgreSQL**, **fastapi-mcp**, and **Playwright**. This service provides remote web page access capabilities with advanced features like proxy support, caching, and HTML-to-Markdown conversion.

## 🚀 Technology Stack

- **FastAPI** - Modern, fast web framework for building APIs
- **PostgreSQL** - Robust relational database for data persistence
- **fastapi-mcp** - Model Context Protocol integration for AI tool connectivity
- **Playwright** - Powerful browser automation library supporting all major browsers
- **SQLModel** - SQL database in Python, designed for simplicity and compatibility
- **Alembic** - Database migration tool

## ✨ Key Features

### 🔄 Proxy Support
- **Dynamic Proxy Pool**: Automatic proxy rotation from API endpoints
- **Static Proxy**: Support for fixed proxy configurations
- **Proxy Validation**: Built-in proxy health checking and validation
- **Flexible Configuration**: Easy switching between proxy types via environment variables

### 💾 Database Caching
- **Request History**: Automatic recording of all web requests and responses
- **Cache Hit Optimization**: Skip redundant requests for previously accessed URLs
- **Performance Metrics**: Track response times and status codes
- **Database Storage**: Persistent cache storage in PostgreSQL

### 🌐 Multi-Browser Support
- **Chrome**: Full Chrome browser automation
- **Firefox**: Complete Firefox browser support
- **Safari**: WebKit-based browser automation
- **Resource Optimization**: Automatic blocking of media resources (images, videos, audio) for improved performance

### 📝 HTML to Markdown Conversion
- **Multiple Parsers**: Support for `html2text` and `markdownify` libraries
- **Configurable Output**: Choose your preferred markdown conversion method
- **Clean Content**: Optimized HTML processing for better markdown output
- **Flexible Integration**: Easy integration with content processing pipelines

## 🎯 Use Cases

### Remote Web Page Access Service
- **Web Scraping**: Extract content from dynamic websites
- **Content Monitoring**: Track changes in web pages over time
- **Data Collection**: Gather structured data from various web sources
- **Performance Testing**: Measure page load times and performance metrics

### MCP (Model Context Protocol) Integration
- **AI Tool Connectivity**: Seamless integration with AI models and tools
- **Automated Web Research**: Enable AI agents to browse and analyze web content
- **Content Processing**: Convert web content to markdown for AI consumption
- **Scalable Architecture**: Handle multiple concurrent requests efficiently

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Recommend at least 6GB RAM available for the service

### Installation & Startup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd playwright-service
   ```

2. **Start the service**
   ```bash
   docker compose up -d
   ```

3. **Access the service**
   - API Documentation: http://localhost:8001/docs
   - Health Check: http://localhost:8001/health
   - MCP Endpoints: http://localhost:8001/mcp/

### Environment Configuration

Create a `.env` file with your configuration:

```env
# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=playwright_service
SERVICE_DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/playwright_service

# Proxy Configuration
PROXY_TYPE=dynamic  # or "static"
PROXY_API_URL=http://your-proxy-api.com/get
PROXY_CHECK_URL=http://httpbin.org/ip
STATIC_PROXY=http://127.0.0.1:8080
```

## 📊 API Endpoints

### Core Service Endpoints
- `POST /html` - Retrieve HTML content from URLs
- `POST /markdown` - Convert web pages to markdown format
- `GET /health` - Service health check
- `GET /management/stats` - Service statistics

### MCP Endpoints
- `POST /mcp/html` - MCP-compatible HTML retrieval
- `POST /mcp/markdown` - MCP-compatible markdown conversion

## 🔧 Configuration Options

### Browser Configuration
- **Browser Type**: Choose between Chrome, Firefox, Safari, or Edge
- **Headless Mode**: Run browsers in headless mode for server environments
- **Timeout Settings**: Configurable page load timeouts
- **Wait Strategies**: Customizable wait conditions for page loading

### Performance Settings
- **Concurrent Requests**: Semaphore-based request limiting
- **Resource Blocking**: Automatic blocking of media resources
- **Memory Management**: Automatic browser cleanup after idle periods
- **Connection Pooling**: Optimized database connection management

## 🛠️ Development

### Local Development Setup
```bash
# Install dependencies
uv sync

# Run database migrations
uv run alembic upgrade head

# Start the development server
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Run tests
uv run pytest

# Run linting
uv run ruff check .
```

## 🔮 Future Roadmap

### Phase 1: Auth
- **Bearer auth**
- **Oauth**
- **Custom auth plugin**

### Phase 2: Frontend Dashboard
- **Web Interface**: Create a comprehensive frontend dashboard
- **Request History Visualization**: Display cached requests and performance metrics
- **Real-time Monitoring**: Live monitoring of service performance
- **Configuration Management**: Web-based configuration interface

### Phase 3: Performance Optimization
- **Request Queuing**: Advanced request queuing and prioritization
- **Load Balancing**: Multi-instance deployment support
- **Caching Strategies**: Redis integration for enhanced caching
- **Resource Optimization**: Memory and CPU usage optimization

### Phase 4: Enhanced HTML Processing
- **Custom Plugins**: Support for custom HTML compression plugins
- **Markdown Parser Optimization**: Improved HTML-to-Markdown conversion
- **Content Extraction**: Advanced content extraction algorithms
- **Format Support**: Additional output formats (JSON, XML, etc.)

## 🤝 Contributing

We welcome contributions! Please feel free to submit issues and pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the health check endpoint at `/health`

---

**Built with ❤️ using FastAPI, Playwright, and modern web technologies**
