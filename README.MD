# Development Guide: Podman, Podman Compose & GitHub

## 1. Prerequisites
- Python 3.13
- Podman & Podman Compose
- Git

## 2. Setup
### Install Podman & Podman Compose
- **Linux:**
	```bash
	sudo apt update
	sudo apt install podman podman-compose
	```
- **Windows:**
	- Use WSL2 (Windows Subsystem for Linux)
	- Follow [Podman Windows install guide](https://podman.io/getting-started/installation)

### Clone the repository
```bash
git clone <your-repo-url>
cd clearviewins6
```

## 3. Building & Running the App
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

## 4. Useful Podman Commands
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

## 5. Useful GitHub Commands
```bash
git status                     # Show changed files
git add .                      # Stage all changes
git commit -m "your message"   # Commit changes
git push                       # Push to remote
git pull                       # Pull latest changes
git log                        # Show commit history
git clone <repo-url>           # Clone a repository
```

## 6. Troubleshooting
- If you change dependencies, rebuild the image:
	```bash
	podman-compose build
	```
- If you want to clean up everything:
	```bash
	podman system prune -a
	```

## 7. See dev_guide_linux.md and dev_guide_windows.md for OS-specific details.
# Podman & Podman Compose Development Guide

## Iterative Development with Podman

Podman is a daemonless container engine for developing, managing, and running OCI Containers. Podman Compose is a tool to help run multi-container applications using Podman.

### Setup
1. Install Podman and Podman Compose:
	- Linux: `sudo apt install podman podman-compose`
	- Windows: Use WSL2 and follow [Podman Windows install guide](https://podman.io/getting-started/installation)

2. Build the image (first time only):
	```bash
	podman build -t clearviewins6 .
	```

3. Start the app for iterative development:
	```bash
	podman-compose up --build
	```
	- Use `--build` to rebuild only changed services.
	- Use `podman-compose down` to stop all containers.

4. For code changes, just restart the relevant service:
	```bash
	podman-compose restart <service_name>
	```

### Useful Podman Commands
```
podman ps                # List running containers
podman images            # List images
podman logs <container>  # View logs
podman exec -it <container> bash  # Open shell in container
podman-compose up        # Start services
podman-compose down      # Stop services
podman-compose restart   # Restart services
```

### Useful GitHub Commands
```
git status
git add .
git commit -m "your message"
git push
git pull
git log
```

## See dev_guide_linux.md and dev_guide_windows.md for more details.
