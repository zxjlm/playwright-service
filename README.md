# Playwright Service

This is a web service based on **FastAPI** and **Playwright** for retrieving HTML content from web pages. The service supports using Chrome and Firefox browsers for page access and provides automatic browser resource management functionality.

## Main Features

- Supports dual browser engines (Chrome and Firefox)
- Automatic browser resource management, auto-cleanup after 10 minutes of idle time
- Supports custom request headers
- Blocks image, audio, video and other media resource loading to improve performance
- Provides health check interfaces
- Returns page status codes and corresponding error messages
