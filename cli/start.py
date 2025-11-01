"""Start module for Reddit Auto Mod - manages all services"""
import os
import sys
import subprocess
import signal
import time
from pathlib import Path
from typing import List, Dict
import threading
import schedule

from cli.config import ConfigManager


class ServiceManager:
    """Manages multiple backend and frontend services"""
    
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.root_dir = Path(__file__).parent.parent
        self.backend_dir = self.root_dir / "BackEnd"
        self.frontend_dir = self.root_dir / "FrontEnd"
        self.running = False
        
    def start_backend_service(self, name: str, script_path: Path, port: int):
        """Start a backend service"""
        try:
            print(f"Starting {name} on port {port}...")
            
            # Start the service
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=script_path.parent,
                text=True,
                bufsize=1
            )
            
            self.processes[name] = process
            print(f"  ✓ {name} started (PID: {process.pid})")
            
            return True
            
        except Exception as e:
            print(f"  ✗ Failed to start {name}: {e}")
            return False
    
    def start_frontend(self):
        """Start the frontend development server"""
        try:
            print("Starting Frontend (React)...")
            
            # Try to detect npm - on Windows it might be npm.cmd
            npm_command = "npm"
            if sys.platform == "win32":
                # On Windows, try npm.cmd first
                try:
                    subprocess.run(["npm.cmd", "--version"], capture_output=True, check=True)
                    npm_command = "npm.cmd"
                    print(f"  Using: {npm_command}")
                except (FileNotFoundError, subprocess.CalledProcessError):
                    # Fall back to npm
                    try:
                        subprocess.run(["npm", "--version"], capture_output=True, check=True)
                        npm_command = "npm"
                        print(f"  Using: {npm_command}")
                    except (FileNotFoundError, subprocess.CalledProcessError):
                        print("  ✗ npm not found in PATH")
                        print("  Please ensure Node.js and npm are installed and in your PATH")
                        print("  Try running 'npm --version' in your terminal")
                        return False
            else:
                # On Unix-like systems, just use npm
                try:
                    subprocess.run(["npm", "--version"], capture_output=True, check=True)
                except (FileNotFoundError, subprocess.CalledProcessError):
                    print("  ✗ npm not found. Please install Node.js and npm.")
                    return False
            
            # Check if node_modules exists
            node_modules = self.frontend_dir / "node_modules"
            if not node_modules.exists():
                print("  Installing frontend dependencies...")
                install_process = subprocess.run(
                    [npm_command, "install"],
                    cwd=self.frontend_dir,
                    capture_output=True,
                    text=True,
                    shell=sys.platform == "win32"
                )
                if install_process.returncode != 0:
                    print(f"  ✗ Failed to install dependencies: {install_process.stderr}")
                    return False
            
            # Start the dev server
            process = subprocess.Popen(
                [npm_command, "run", "dev"],
                cwd=self.frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                shell=sys.platform == "win32"
            )
            
            self.processes["frontend"] = process
            print(f"  ✓ Frontend started (PID: {process.pid})")
            print("  Frontend will be available at: http://localhost:5173")
            
            return True
            
        except FileNotFoundError as e:
            print(f"  ✗ npm not found: {e}")
            print("  Please install Node.js and npm.")
            return False
        except Exception as e:
            print(f"  ✗ Failed to start frontend: {e}")
            return False
    
    def start_all_services(self):
        """Start all backend services and frontend"""
        print()
        print("=" * 60)
        print("Starting Reddit Auto Mod Services")
        print("=" * 60)
        print()
        
        # Check if setup is complete
        config_manager = ConfigManager()
        if not config_manager.config_exists():
            print("ERROR: Configuration not found.")
            print("Please run 'reddit-auto-mod config' first.")
            return False
        
        config = config_manager.load_config()
        if 'subreddits' not in config or not config['subreddits']:
            print("ERROR: Subreddits not configured.")
            print("Please run 'reddit-auto-mod setup' first.")
            return False
        
        # Define services to start
        services = [
            {
                "name": "Fetch Data API",
                "path": self.backend_dir / "ControlPlane" / "FetchDataAPI.py",
                "port": 8000
            },
            {
                "name": "Text Summarization",
                "path": self.backend_dir / "DataProcessingPlane" / "PostSummarization" / "TextSummarization.py",
                "port": 8002
            },
            {
                "name": "Rule Violation",
                "path": self.backend_dir / "DataProcessingPlane" / "RuleViolation" / "RuleViolation.py",
                "port": 8003
            },
            {
                "name": "Post Similarity",
                "path": self.backend_dir / "DataProcessingPlane" / "PostSimilarity" / "PostSimilarity.py",
                "port": 8004
            },
            {
                "name": "Data Processing API",
                "path": self.backend_dir / "DataProcessingPlane" / "DataProcessingAPI.py",
                "port": 8001
            }
        ]
        
        # Start backend services
        print("Starting Backend Services...")
        print("-" * 60)
        
        for service in services:
            if not service["path"].exists():
                print(f"  ✗ {service['name']}: Script not found at {service['path']}")
                continue
            
            success = self.start_backend_service(
                service["name"],
                service["path"],
                service["port"]
            )
            
            if not success:
                print("Failed to start all services. Cleaning up...")
                self.stop_all_services()
                return False
            
            # Give the service time to start
            time.sleep(2)
        
        print()
        
        # Start frontend
        print("Starting Frontend...")
        print("-" * 60)
        
        if not self.start_frontend():
            print()
            print("ERROR: Failed to start frontend. Frontend is required.")
            print("Please install Node.js and npm:")
            print("  Download from: https://nodejs.org/")
            print()
            print("Stopping all services...")
            self.stop_all_services()
            return False
        
        print()
        print("=" * 60)
        print("✓ All services started successfully!")
        print("=" * 60)
        print()
        print("Service URLs:")
        print("  Frontend:             http://localhost:5173")
        print("  Fetch Data API:       http://localhost:8000")
        print("  Data Processing API:  http://localhost:8001")
        print("  Summarization API:    http://localhost:8002")
        print("  Rule Violation API:   http://localhost:8003")
        print("  Similarity API:       http://localhost:8004")
        print()
        print("Press Ctrl+C to stop all services")
        print()
        
        self.running = True
        return True
    
    def stop_all_services(self):
        """Stop all running services"""
        print()
        print("Stopping all services...")
        
        for name, process in self.processes.items():
            try:
                print(f"  Stopping {name}...")
                process.terminate()
                process.wait(timeout=5)
                print(f"  ✓ {name} stopped")
            except subprocess.TimeoutExpired:
                print(f"  Force killing {name}...")
                process.kill()
            except Exception as e:
                print(f"  Error stopping {name}: {e}")
        
        self.processes.clear()
        self.running = False
        print("All services stopped.")
    
    def monitor_services(self):
        """Monitor service health and restart if needed"""
        while self.running:
            time.sleep(10)
            
            # Check if any process has died
            for name, process in list(self.processes.items()):
                if process.poll() is not None:
                    print(f"\n  WARNING: {name} has stopped unexpectedly (exit code: {process.returncode})")
                    # Optionally restart the service here
            
            # Check for new output from processes
            for name, process in self.processes.items():
                if process.stdout:
                    line = process.stdout.readline()
                    if line:
                        print(f"[{name}] {line.strip()}")


def run_daily_processing():
    """Run the data processing job"""
    print()
    print("=" * 60)
    print(f"Running scheduled data processing - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        import requests
        from cli.config import ConfigManager
        
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        if not config:
            print("ERROR: Configuration not found")
            return
        
        # Get credentials and subreddits
        credentials = config.get('reddit_credentials')
        subreddits = config.get('subreddits', [])
        
        if not credentials or not subreddits:
            print("ERROR: Credentials or subreddits not configured")
            return
        
        # Prepare payload
        payload = {
            "credentials": {
                "client_id": credentials['client_id'],
                "client_secret": credentials['client_secret'],
                "user_agent": credentials['user_agent'],
                "user_name": credentials['username'],
                "password": credentials['password']
            },
            "subredditList": subreddits
        }
        
        # Call the data processing API
        print(f"Processing subreddits: {', '.join(subreddits)}")
        
        response = requests.post(
            "http://localhost:8001/initiateProcesing",
            json=payload,
            timeout=300  # 5 minute timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Processing completed successfully")
            print(f"  Message: {result.get('Message')}")
        else:
            print(f"✗ Processing failed with status {response.status_code}")
            print(f"  Response: {response.text}")
    
    except requests.exceptions.RequestException as e:
        print(f"✗ Error calling data processing API: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    print("=" * 60)
    print()


def wait_for_services():
    """Wait for all services to be ready"""
    import requests
    
    services = [
        ("Data Processing API", "http://localhost:8001/health"),
        ("Summarization API", "http://localhost:8002/health"),
        ("Rule Violation API", "http://localhost:8003/health"),
        ("Similarity API", "http://localhost:8004/health"),
    ]
    
    print("Waiting for services to be ready...")
    max_wait = 30  # Maximum wait time in seconds
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        all_ready = True
        for name, url in services:
            try:
                response = requests.get(url, timeout=1)
                if response.status_code != 200:
                    all_ready = False
                    break
            except requests.exceptions.RequestException:
                all_ready = False
                break
        
        if all_ready:
            print("✓ All services are ready!")
            return True
        
        time.sleep(2)
    
    print("⚠ Some services may not be ready yet")
    return False


def start_scheduler():
    """Start the daily processing scheduler"""
    print()
    print("Starting daily processing scheduler...")
    print("  Job will run every day at 00:00 (midnight)")
    print()
    
    # Schedule the job
    schedule.every().day.at("00:00").do(run_daily_processing)
    
    # Run immediately on startup (optional)
    response = input("Do you want to run data processing now? (y/n): ").strip().lower()
    if response == 'y':
        # Wait for services to be ready before running
        if wait_for_services():
            run_daily_processing()
        else:
            print("⚠ Skipping immediate run - services not ready")
            print("  Processing will still run at scheduled time (00:00)")
    
    # Run scheduler in background thread
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    print("✓ Scheduler started")


def start_all():
    """Start all services including scheduler"""
    service_manager = ServiceManager()
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        print()
        print("Received shutdown signal...")
        service_manager.stop_all_services()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start all services
    if not service_manager.start_all_services():
        print("Failed to start services. Exiting...")
        sys.exit(1)
    
    # Start scheduler
    start_scheduler()
    
    # Monitor services
    try:
        service_manager.monitor_services()
    except KeyboardInterrupt:
        print()
        print("Shutting down...")
        service_manager.stop_all_services()
    except Exception as e:
        print(f"Error: {e}")
        service_manager.stop_all_services()
        sys.exit(1)


def show_status():
    """Show status of all services"""
    import requests
    
    print()
    print("=" * 60)
    print("Service Status")
    print("=" * 60)
    print()
    
    services = [
        ("Fetch Data API", "http://localhost:8000/health"),
        ("Data Processing API", "http://localhost:8001/health"),
        ("Summarization API", "http://localhost:8002/health"),
        ("Rule Violation API", "http://localhost:8003/health"),
        ("Similarity API", "http://localhost:8004/health"),
    ]
    
    for name, url in services:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print(f"✓ {name}: Running")
            else:
                print(f"✗ {name}: Unhealthy (status {response.status_code})")
        except requests.exceptions.RequestException:
            print(f"✗ {name}: Not running")
    
    # Check frontend
    try:
        response = requests.get("http://localhost:5173", timeout=2)
        print(f"✓ Frontend: Running")
    except requests.exceptions.RequestException:
        print(f"✗ Frontend: Not running")
    
    print()
