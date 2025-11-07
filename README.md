# ACEestFitness and Gym - Web Application

A modern, responsive web application for tracking fitness workouts, converted from a Tkinter GUI application to a Flask web application for containerized deployment.

## Features

- **Add Workouts**: Log workout names and duration in minutes
- **View Workouts**: Display all logged workouts with statistics
- **Persistent Storage**: Data is saved to JSON file and persists between sessions
- **Responsive Design**: Modern Bootstrap-based UI that works on all devices
- **REST API**: JSON API endpoints for programmatic access
- **Statistics**: View total workouts and total minutes exercised
- **Data Management**: Clear all workouts functionality
- **Container Ready**: Dockerized for easy deployment

### Technologies Used

- **Backend**: Flask (Python web framework)
- **Frontend**: HTML5, CSS3, Bootstrap 5, Font Awesome
- **Data Storage**: JSON file-based persistence
- **Containerization**: Docker & Docker Compose
- **Testing**: Pytest
- **Production Server**: Gunicorn WSGI server

## Quick Start

### Option 1: Using Docker (Recommended)

1. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

2. **Access the application:**
   Open your browser to `http://localhost:5000`

### Option 2: Using Docker directly

1. **Build the Docker image:**
   ```bash
   docker build -t aceest-fitness .
   ```

2. **Run the container:**
   ```bash
   docker run -p 5000:5000 -v $(pwd)/data:/app/data aceest-fitness
   ```

### Option 3: Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   # Development mode
   export FLASK_ENV=development
   python app.py
   
   # Or use the startup script
   ./start.sh
   ```

3. **Access the application:**
   Open your browser to `http://localhost:5000`

## API Endpoints

The application provides REST API endpoints for programmatic access:

### Get All Workouts
```http
GET /api/workouts
```
Returns: JSON array of all workouts

### Add a Workout
```http
POST /api/workouts
Content-Type: application/json

{
  "workout": "Push-ups",
  "duration": 30
}
```
Returns: Success message with created workout

### Clear All Workouts
```http
DELETE /api/workouts
```
Returns: Success confirmation message

## Application Structure

```
aceest-fitness-new/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── Dockerfile           # Container configuration
├── docker-compose.yml   # Multi-container setup
├── start.sh            # Startup script
├── test_app.py         # Test suite
├── templates/          # HTML templates
│   ├── index.html     # Main application page
│   └── error.html     # Error page template
├── data/              # Data directory (created at runtime)
│   └── workouts.json  # Workout data storage
└── README.md          # This file
```

## Configuration

The application supports different environments through configuration:

- **Development**: Debug mode enabled, local file storage
- **Production**: Optimized for deployment, security headers
- **Testing**: Isolated environment for testing

### Environment Variables

- `FLASK_ENV`: Set to 'development' or 'production'
- `SECRET_KEY`: Flask secret key (change in production)
- `DATA_DIR`: Directory for data storage (default: 'data')
- `WORKOUTS_FILE`: Filename for workout data (default: 'workouts.json')

## Testing

Run the test suite:

```bash
# Install test dependencies (if not already installed)
pip install pytest pytest-cov

# Run tests
pytest

# Run tests with coverage
pytest --cov=app test_app.py
```

## Development

### Adding New Features

1. **Backend**: Modify `app.py` to add new routes and functionality
2. **Frontend**: Update `templates/index.html` for UI changes
3. **API**: Add new endpoints following REST conventions
4. **Tests**: Add corresponding tests in `test_app.py`

### Code Style

- Follow PEP 8 for Python code
- Use semantic HTML and modern CSS practices
- Maintain responsive design principles

## Production Deployment

### Docker Deployment

The application is containerized and production-ready:

1. **Environment Variables**: Set production environment variables
2. **Secrets**: Change the default secret key
3. **Data Persistence**: Mount volume for data directory
4. **Health Checks**: Built-in health check endpoint
5. **Security**: Non-root user, security headers

### Cloud Deployment

The containerized application can be deployed to:
- **Docker Swarm**
- **Kubernetes**
- **AWS ECS/Fargate**
- **Google Cloud Run**
- **Azure Container Instances**
- **Heroku** (with Dockerfile)

### Example Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aceest-fitness
spec:
  replicas: 3
  selector:
    matchLabels:
      app: aceest-fitness
  template:
    metadata:
      labels:
        app: aceest-fitness
    spec:
      containers:
      - name: aceest-fitness
        image: aceest-fitness:latest
        ports:
        - containerPort: 5000
        env:
        - name: FLASK_ENV
          value: "production"
        volumeMounts:
        - name: data-volume
          mountPath: /app/data
      volumes:
      - name: data-volume
        persistentVolumeClaim:
          claimName: fitness-data-pvc
```

## Migration from Tkinter

This web application maintains the same core functionality as the original Tkinter application:

- ✅ Add workouts with name and duration
- ✅ View all logged workouts
- ✅ Input validation
- ✅ Persistent data storage
- ✅ User-friendly interface
- ➕ **Additional web features:**
  - Responsive design for mobile devices
  - REST API for integration
  - Statistics dashboard
  - Modern, professional UI
  - Container deployment ready
  - Multi-user capability (with future authentication)

## Troubleshooting

### Common Issues

1. **Port already in use**: Change the port in docker-compose.yml or use a different port
2. **Permission denied**: Ensure Docker has proper permissions
3. **Data not persisting**: Check volume mounts in Docker setup

### Logs

View application logs:
```bash
# Docker Compose
docker-compose logs -f

# Docker
docker logs <container-id>
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For support and questions:
- Create an issue in the GitHub repository
- Check the troubleshooting section
- Review the API documentation above

## CI/CD (Jenkins + SonarQube + Minikube)

This repository includes a `Jenkinsfile` that automates the full pipeline:

1. Checkout source
2. Create Python virtual environment & install dependencies
3. Run pytest with coverage producing `coverage.xml` and JUnit XML
4. Run SonarQube static analysis and publish coverage to Sonar
5. Enforce SonarQube Quality Gate (fail fast if not passed)
6. Build Docker image
7. Build image again inside Minikube Docker daemon (so no external registry needed)
8. Apply Kubernetes manifests (`k8s/deployment.yaml`, `k8s/service.yaml`)
9. Smoke test the deployed service via `curl` and verify page content

### Required Jenkins Plugins

- Pipeline
- SonarQube Scanner
- JUnit
- Credentials Binding (if using tokens)

### SonarQube Setup

1. Install SonarQube (local or remote).
2. Generate a project token.
3. In Jenkins, configure SonarQube under Manage Jenkins > Configure System. Name it the same as `SONARQUBE_ENV` in `Jenkinsfile` (default: `SonarQubeServer`).
4. Optionally store token as a secret credential; the scanner will use Jenkins global config.

### Minikube Requirements

Ensure the Jenkins agent/node has access to the Minikube environment. If Jenkins runs on your laptop, simply start Minikube before running the pipeline:

```bash
minikube start
```

### Manual Verification Steps

```bash
eval $(minikube docker-env)
docker build -t aceest-fitness:latest .
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl rollout status deployment/aceest-fitness
minikube service aceest-fitness --url
```

### Adjustments

- Change `nodePort` in `k8s/service.yaml` if 30080 conflicts.
- Add resource requests/limits for production.
- Add secrets/config maps for environment-specific settings.
- Add a staging namespace and promote only after quality gate success.

### Extending the Pipeline

Potential enhancements:

- Add Snyk or Trivy scan stage for dependency/container security.
- Push image to a registry (Docker Hub, GHCR) instead of relying on Minikube daemon.
- Add Slack notifications on failure/success.
- Add performance test stage using Locust.

## Docker Image Publishing (Jenkins)

The pipeline now builds and publishes a Docker image to Docker Hub after passing tests and the SonarQube Quality Gate.

### Image Tags

- `latest` – Always points to the most recent successful build on the default branch.
- `<short-sha>` – 8-character Git commit identifier for immutable deployments.

Example pushed images:

```
2025ht66019/aceest_fitness:latest
2025ht66019/aceest_fitness:3fa92c1d
```

### Using the Image Locally

```bash
docker pull 2025ht66019/aceest_fitness:latest
docker run -p 5000:5000 2025ht66019/aceest_fitness:latest
```

### Updating Credentials in Jenkins

1. Navigate to Jenkins > Manage Jenkins > Credentials.
2. Add a credential of type Username/Password with your Docker Hub username and a personal access token/password.
3. Set the ID to `dockerhub-creds` (or adjust in `Jenkinsfile`).

### Forcing a Rebuild

If dependencies changed but Docker layer cache is stuck, run a build with the option `--no-cache` locally or temporarily modify the pipeline to add:

```groovy
sh "docker build --no-cache -t ${tagCommit} -t ${tagLatest} ."
```

### Verifying Push

After a successful pipeline run, confirm image availability:

```bash
curl -s https://hub.docker.com/v2/repositories/2025ht66019/aceest_fitness/tags/ | jq '.results[].name'
```

Or simply pull the commit tag:

```bash
docker pull 2025ht66019/aceest_fitness:<short-sha>
```

### Deployment Example (Kubernetes)

```yaml
containers:
  - name: aceest-fitness
    image: 2025ht66019/aceest_fitness:latest
    ports:
      - containerPort: 5000
```

Use the commit tag for rollbacks:

```yaml
image: 2025ht66019/aceest_fitness:3fa92c1d
```

### Security Scanning (Optional Next Step)

Add a stage with Trivy:

```groovy
stage('Trivy Scan') {
  steps {
    sh 'trivy image --exit-code 0 --severity HIGH,CRITICAL ${env.DOCKER_IMAGE_COMMIT}'
  }
}
```

---
The Docker build/push occurs only after a successful test and (if applicable) SonarQube Quality Gate pass, ensuring only high-quality images reach the registry.

---

For any CI/CD related issues, inspect Jenkins build logs with timestamps and color enabled (already configured in pipeline options).