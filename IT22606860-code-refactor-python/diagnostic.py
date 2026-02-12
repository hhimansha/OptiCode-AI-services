"""
IT22606860 - System Diagnostic Tool
Checks if all prerequisites and connections are properly configured
"""

import sys
import subprocess
import socket
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*80)
    print(f" {text}")
    print("="*80)

def check_command(command, name):
    """Check if a command exists and get version"""
    try:
        result = subprocess.run(
            [command, '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.split('\n')[0] if result.stdout else result.stderr.split('\n')[0]
            print(f"✅ {name:20} {version}")
            return True
        else:
            print(f"❌ {name:20} NOT FOUND")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        print(f"❌ {name:20} NOT FOUND ({type(e).__name__})")
        return False

def check_port(port, service_name):
    """Check if a port is in use (service is running)"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    
    status = "✅ RUNNING" if result == 0 else "❌ NOT RUNNING"
    print(f"{status:15} Port {port:5} - {service_name}")
    return result == 0

def check_file(file_path, description):
    """Check if a file exists"""
    path = Path(file_path)
    exists = path.exists()
    status = "✅" if exists else "❌"
    print(f"{status} {description:50} {'EXISTS' if exists else 'MISSING'}")
    return exists

def check_python_package(package_name):
    """Check if a Python package is installed"""
    try:
        __import__(package_name)
        print(f"✅ {package_name:30} installed")
        return True
    except ImportError:
        print(f"❌ {package_name:30} NOT installed")
        return False

def main():
    """Run all diagnostic checks"""
    
    print_header("IT22606860 - SYSTEM DIAGNOSTIC TOOL")
    
    # Get project root
    script_dir = Path(__file__).parent.parent.parent.parent
    
    # =========================================
    # 1. CHECK PREREQUISITES
    # =========================================
    print_header("1. Checking Prerequisites")
    
    prereq_checks = {
        'python': check_command('python', 'Python'),
        'node': check_command('node', 'Node.js'),
        'npm': check_command('npm', 'npm'),
    }
    
    # =========================================
    # 2. CHECK PYTHON PACKAGES
    # =========================================
    print_header("2. Checking Python Packages")
    
    required_packages = [
        'flask',
        'flask_cors',
        'openai',
        'transformers',
        'torch',
        'astor',
        'bandit',
        'radon',
        'pylint',
    ]
    
    package_checks = {pkg: check_python_package(pkg) for pkg in required_packages}
    
    # =========================================
    # 3. CHECK PROJECT FILES
    # =========================================
    print_header("3. Checking Project Files")
    
    important_files = {
        'refactor_api': script_dir / 'backend' / 'OptiCode-AI-services' / 'IT22606860-code-refactor-python' / 'refactor_api_fast.py',
        'risk_api': script_dir / 'backend' / 'OptiCode-AI-services' / 'IT22606860-code-refactor-python' / 'risk_analysis_api.py',
        'learning_api': script_dir / 'backend' / 'OptiCode-AI-services' / 'IT22606860-code-refactor-python' / 'learning_api.py',
        'express_server': script_dir / 'frontend' / 'OptiCode' / 'server' / 'server.js',
        'react_main': script_dir / 'frontend' / 'OptiCode' / 'client' / 'src' / 'main.jsx',
        'startup_script': script_dir / 'backend' / 'OptiCode-AI-services' / 'IT22606860-code-refactor-python' / 'start_all_services.py',
    }
    
    file_checks = {}
    for name, path in important_files.items():
        file_checks[name] = check_file(str(path), f"{name:30}")
    
    # =========================================
    # 4. CHECK SERVICES
    # =========================================
    print_header("4. Checking Running Services")
    
    services = {
        8000: 'Python Refactoring API',
        8001: 'Python Risk Analysis API',
        8002: 'Python Learning API',
        5000: 'Express Backend Server',
        5173: 'React Frontend (Vite)',
    }
    
    service_checks = {port: check_port(port, name) for port, name in services.items()}
    
    # =========================================
    # 5. CHECK CONFIGURATION FILES
    # =========================================
    print_header("5. Checking Configuration Files")
    
    config_files = {
        'python_env': script_dir / 'backend' / 'OptiCode-AI-services' / 'IT22606860-code-refactor-python' / '.env',
        'server_env': script_dir / 'frontend' / 'OptiCode' / 'server' / '.env',
        'client_env': script_dir / 'frontend' / 'OptiCode' / 'client' / '.env',
        'requirements': script_dir / 'backend' / 'OptiCode-AI-services' / 'IT22606860-code-refactor-python' / 'requirements.txt',
        'server_package': script_dir / 'frontend' / 'OptiCode' / 'server' / 'package.json',
        'client_package': script_dir / 'frontend' / 'OptiCode' / 'client' / 'package.json',
    }
    
    config_checks = {}
    for name, path in config_files.items():
        config_checks[name] = check_file(str(path), f"{name:30}")
    
    # =========================================
    # 6. GENERATE REPORT
    # =========================================
    print_header("DIAGNOSTIC REPORT")
    
    total_checks = 0
    passed_checks = 0
    
    # Count prerequisites
    total_checks += len(prereq_checks)
    passed_checks += sum(prereq_checks.values())
    
    # Count packages
    total_checks += len(package_checks)
    passed_checks += sum(package_checks.values())
    
    # Count files
    total_checks += len(file_checks)
    passed_checks += sum(file_checks.values())
    
    # Count services
    total_checks += len(service_checks)
    passed_checks += sum(service_checks.values())
    
    # Count configs
    total_checks += len(config_checks)
    passed_checks += sum(config_checks.values())
    
    print(f"\n✅ Passed: {passed_checks}/{total_checks} checks")
    print(f"❌ Failed: {total_checks - passed_checks}/{total_checks} checks")
    
    # Provide recommendations
    if passed_checks == total_checks:
        print("\n🎉 ALL CHECKS PASSED! System is ready to run.")
    else:
        print("\n⚠️  ISSUES DETECTED:")
        
        if not all(prereq_checks.values()):
            print("\n   Missing Prerequisites:")
            for name, status in prereq_checks.items():
                if not status:
                    print(f"   • Install {name}")
        
        if not all(package_checks.values()):
            print("\n   Missing Python Packages:")
            print("   • Run: pip install -r requirements.txt")
        
        if not all(service_checks.values()):
            print("\n   Services Not Running:")
            print("   • Run: python start_all_services.py")
            print("   • Or use: start_all.bat")
        
        if not all(config_checks.values()):
            print("\n   Missing Configuration Files:")
            for name, status in config_checks.items():
                if not status and 'env' in name:
                    print(f"   • Copy .env.example to .env")
    
    print("\n" + "="*80)
    
    return passed_checks == total_checks

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
