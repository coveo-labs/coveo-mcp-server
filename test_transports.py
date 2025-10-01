#!/usr/bin/env python3
"""
Transport Testing Script for Coveo MCP Server

This script tests all available transport modes to ensure they are working correctly:
- streamable-http (default)
- SSE (legacy)
- STDIO (direct communication)

Usage:
    python test_transports.py
"""

import subprocess
import time
import os
import sys
from typing import Tuple


def test_transport_mode(mode: str, env_vars: dict = None) -> Tuple[bool, str]:
    """
    Test a specific transport mode.
    
    Args:
        mode: Description of the transport mode being tested
        env_vars: Environment variables to set for this test
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    print(f"Testing {mode}...")
    
    # Prepare environment
    test_env = os.environ.copy()
    if env_vars:
        test_env.update(env_vars)
    
    try:
        # Start the server process
        proc = subprocess.Popen(
            ['python', '-m', 'coveo_mcp_server'], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True,
            env=test_env
        )
        
        # Wait for startup
        time.sleep(2)
        
        # Check if process is still running (indicates successful startup)
        if proc.poll() is None:
            # Process is running, terminate it
            proc.terminate()
            proc.wait(timeout=5)
            return True, f"✅ {mode}: SUCCESS"
        else:
            # Process exited, capture output for debugging
            stdout, _ = proc.communicate()
            return False, f"❌ {mode}: FAILED - Process exited early\nOutput: {stdout}"
            
    except subprocess.TimeoutExpired:
        # Process didn't terminate gracefully, kill it
        proc.kill()
        proc.wait()
        return True, f"✅ {mode}: SUCCESS (had to force kill)"
    except Exception as e:
        return False, f"❌ {mode}: FAILED - Exception: {str(e)}"


def test_stdio_import() -> Tuple[bool, str]:
    """
    Test STDIO transport by checking if the server can be imported.
    We don't start the STDIO server as it would block waiting for input.
    """
    print("Testing STDIO transport import...")
    
    try:
        result = subprocess.run(
            ['python', '-c', 'from coveo_mcp_server.server import mcp; print("STDIO import works")'], 
            check=True, 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        
        if "STDIO import works" in result.stdout:
            return True, "✅ STDIO transport: SUCCESS"
        else:
            return False, f"❌ STDIO transport: FAILED - Unexpected output: {result.stdout}"
            
    except subprocess.CalledProcessError as e:
        return False, f"❌ STDIO transport: FAILED - Process error: {e.stderr}"
    except subprocess.TimeoutExpired:
        return False, "❌ STDIO transport: FAILED - Import timeout"
    except Exception as e:
        return False, f"❌ STDIO transport: FAILED - Exception: {str(e)}"


def main():
    """Main test function."""
    print("🧪 Testing all transport modes for Coveo MCP Server...")
    print("=" * 60)
    
    results = []
    
    # Test streamable-http (default)
    success, message = test_transport_mode("streamable-http transport (default)")
    results.append((success, message))
    print(message)
    
    print()
    
    # Test SSE transport
    success, message = test_transport_mode("SSE transport", {"USE_SSE": "true"})
    results.append((success, message))
    print(message)
    
    print()
    
    # Test STDIO transport (import only)
    success, message = test_stdio_import()
    results.append((success, message))
    print(message)
    
    print()
    print("=" * 60)
    
    # Summary
    passed = sum(1 for success, _ in results if success)
    total = len(results)
    
    if passed == total:
        print(f"🎉 All {total} transport modes tested successfully!")
        sys.exit(0)
    else:
        print(f"⚠️  {passed}/{total} transport modes passed")
        print("\nFailed tests:")
        for success, message in results:
            if not success:
                print(f"  {message}")
        sys.exit(1)


if __name__ == "__main__":
    main()