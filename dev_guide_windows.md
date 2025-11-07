
# Podman & Podman Compose for Windows

## 1. Prerequisites
- Python 3.13
- Podman & Podman Compose
- Git

## 2. Install Podman & Podman Compose
1. Use WSL2 (Windows Subsystem for Linux)
2. Follow [Podman Windows install guide](https://podman.io/getting-started/installation)

## 3. Clone the repository
```bash
git clone <your-repo-url>
cd clearviewins6
```

## 4. Building & Running the App
### Build the image (first time only)
```bash
podman build -t clearviewins6 .
```

### Start the app (iterative development)
```bash
podman-compose up --build
```
- Use `--build` to rebuild only changed services.
- Use `podman-compose down` to stop all containers.
- For code changes, just restart the relevant service:
	```bash
	podman-compose restart web
	```

### Access the app
- Open your browser at [http://localhost:5000](http://localhost:5000)

## 5. Useful Podman Commands
```bash
podman ps                      # List running containers
podman images                  # List images
podman logs <container>        # View logs for a container
podman exec -it <container> bash  # Open shell in container
podman-compose up              # Start services
podman-compose down            # Stop services
podman-compose restart <service> # Restart a service
podman system prune            # Remove unused containers, images, volumes
podman volume prune            # Remove unused volumes
podman image prune             # Remove unused images
podman container prune         # Remove stopped containers
```

## 6. Useful GitHub Commands
```bash
git status                     # Show changed files
git add .                      # Stage all changes
git commit -m "your message"   # Commit changes
git push                       # Push to remote
git pull                       # Pull latest changes
git log                        # Show commit history
git clone <repo-url>           # Clone a repository
```

## 7. Troubleshooting
- If you change dependencies, rebuild the image:
	```bash
	podman-compose build
	```
- If you want to clean up everything:
	```bash
	podman system prune -a
	```
