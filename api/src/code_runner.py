import subprocess
import tempfile
import os
import logging
from typing import Tuple, Dict, Optional

logger = logging.getLogger(__name__)

NSJAIL_CONFIG_PATH = "/app/nsjail.cfg"

def compile_cpp(code: str) -> Tuple[Optional[str], Optional[str]]:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as source_file:
        source_file.write(code)
        source_path = source_file.name

    executable_path = source_path.replace('.cpp', '.out')
    
    try:
        cmd = ["g++", "-O2", "-o", executable_path, source_path]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return None, result.stderr
            
        return executable_path, None

    except subprocess.TimeoutExpired:
        return None, "Compilation timed out."
    except Exception as e:
        return None, f"Internal compilation error: {str(e)}"
    finally:
        # Clean source file
        if os.path.exists(source_path):
            os.remove(source_path)

def run_cpp_executable(executable_path: str, input_str: str) -> Dict:
    """
    Runs a compiled C++ executable inside nsjail.
    
    Args:
        executable_path (str): Path to the compiled executable.
        input_str (str): Input to provide via stdin.
        
    Returns:
        Dict: {'stdout': str, 'stderr': str, 'exit_code': int, 'status': str}
    """
    if not os.path.exists(executable_path):
        return {
            "stdout": "",
            "stderr": "Executable not found.",
            "exit_code": -1,
            "status": "internal_error"
        }

    try:
        
        cmd = [
            "nsjail",
            "--config", NSJAIL_CONFIG_PATH,
            "--really_quiet",
            "--bindmount_ro", f"{executable_path}:/sandbox/program",
            "--",
            "/sandbox/program"
        ]

        logger.info(f"Running command: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            input=input_str,
            text=True,
            capture_output=True,
            timeout=5 
        )
        
        status = "success" if result.returncode == 0 else "runtime_error"
        if result.returncode != 0 and "TIME LIMIT" in result.stderr:
            status = "timeout"

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
            "status": status
        }

    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": "Execution timed out (subprocess)",
            "exit_code": -1,
            "status": "timeout"
        }
    except FileNotFoundError:
        return {
            "stdout": "",
            "stderr": "System Configuration Error: nsjail executable not found. Please contact administrator.",
            "exit_code": -1,
            "status": "system_error"
        }
    except Exception as e:
        logger.error(f"Error running code: {e}")
        return {
            "stdout": "",
            "stderr": f"System Error: {str(e)}",
            "exit_code": -1,
            "status": "system_error"
        }
