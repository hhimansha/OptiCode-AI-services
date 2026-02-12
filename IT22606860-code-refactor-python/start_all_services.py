"""
Unified Service Launcher for IT22606860 Code Refactoring Platform
Starts all three Flask APIs on separate ports:
- Refactoring API (port 8000)
- Risk Analysis API (port 8001)
- Learning Content API (port 8002)
"""
import subprocess
import sys
import os
import time
import signal
from pathlib import Path

# Store process references for cleanup
processes = []

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n" + "="*80)
    print("🛑 Shutting down all services...")
    print("="*80)
    for process in processes:
        try:
            process.terminate()
        except:
            pass
    sys.exit(0)

# Register signal handler
signal.signal(signal.SIGINT, signal_handler)

def check_port(port):
    """Check if a port is already in use"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result == 0

def start_service(script_name, port, service_name):
    """Start a Flask service"""
    print(f"\n🚀 Starting {service_name} on port {port}...")
    
    if check_port(port):
        print(f"⚠️  Port {port} is already in use. Service may already be running.")
        return None
    
    try:
        # Use python -u for unbuffered output
        process = subprocess.Popen(
            [sys.executable, '-u', script_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Give it a moment to start
        time.sleep(2)
        
        if process.poll() is None:
            print(f"✅ {service_name} started successfully")
            return process
        else:
            print(f"❌ {service_name} failed to start")
            return None
            
    except Exception as e:
        print(f"❌ Error starting {service_name}: {e}")
        return None

def main():
    """Main startup routine"""
    print("="*80)
    print(" 🎯 IT22606860 - CODE REFACTORING PLATFORM")
    print(" Starting All Backend Services")
    print("="*80)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Check Python version
    print(f"\n📍 Python Version: {sys.version}")
    print(f"📁 Working Directory: {os.getcwd()}")
    
    # Service configurations
    services = [
        {
            'script': 'refactor_api_fast.py',
            'port': 8000,
            'name': 'Refactoring API (Fast)',
            'description': '100+ Refactoring Patterns, Architecture Analysis'
        },
        {
            'script': 'risk_analysis_api.py',
            'port': 8001,
            'name': 'Risk Analysis API',
            'description': 'AI-Powered Risk Assessment'
        },
        {
            'script': 'learning_api.py',
            'port': 8002,
            'name': 'Learning Content API',
            'description': '50+ Educational Topics'
        }
    ]
    
    print("\n" + "="*80)
    print(" 📋 SERVICES TO START:")
    print("="*80)
    for service in services:
        print(f"  • {service['name']:25} - Port {service['port']} - {service['description']}")
    print("="*80)
    
    # Start each service
    for service in services:
        process = start_service(
            service['script'],
            service['port'],
            service['name']
        )
        if process:
            processes.append(process)
        time.sleep(1)
    
    if not processes:
        print("\n❌ No services were started successfully!")
        sys.exit(1)
    
    # Display success summary
    print("\n" + "="*80)
    print(" ✅ ALL SERVICES RUNNING")
    print("="*80)
    print("\n📍 Service Endpoints:")
    for service in services:
        if any(p for p in processes):
            print(f"  • {service['name']:25} http://localhost:{service['port']}")
    
    print("\n" + "="*80)
    print(" 🎯 API ENDPOINTS AVAILABLE:")
    print("="*80)
    print("\n📦 Refactoring API (Port 8000):")
    print("  POST /api/refactor              - Basic refactoring")
    print("  POST /api/priority-refactor     - Top 20 patterns (FASTEST)")
    print("  POST /api/advanced-refactor     - 100+ patterns")
    print("  POST /api/architecture-analyze  - Architecture analysis")
    print("  POST /api/generate-tests        - Generate tests")
    print("  GET  /health                    - Health check")
    
    print("\n🔍 Risk Analysis API (Port 8001):")
    print("  POST /api/analyze-risks         - Analyze code risks")
    print("  GET  /health                    - Health check")
    
    print("\n📚 Learning API (Port 8002):")
    print("  GET  /api/topics                - List all topics")
    print("  GET  /api/topic/<name>          - Get topic details")
    print("  GET  /health                    - Health check")
    
    print("\n" + "="*80)
    print(" 💡 USAGE:")
    print("="*80)
    print("  • Frontend should connect to: http://localhost:8000")
    print("  • Express middleware should proxy to these ports")
    print("  • Press Ctrl+C to stop all services")
    print("="*80 + "\n")
    
    # Keep the script running and monitor processes
    try:
        while True:
            time.sleep(1)
            # Check if any process has died
            for i, process in enumerate(processes):
                if process.poll() is not None:
                    print(f"\n⚠️  Service {i+1} has stopped unexpectedly!")
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == '__main__':
    main()
