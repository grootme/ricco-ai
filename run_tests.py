#!/usr/bin/env python3
"""
OpenClaw Agent SaaS - Test Runner

Script para ejecutar la suite de tests con diferentes configuraciones.
Incluye soporte para tests unitarios, de integración y con API real.

Uso:
    python run_tests.py                    # Ejecutar todos los tests
    python run_tests.py --unit             # Solo tests unitarios
    python run_tests.py --integration      # Solo tests de integración
    python run_tests.py --coverage         # Con reporte de cobertura
    python run_tests.py --verbose          # Output detallado
    python run_tests.py --file test_x.py   # Archivo específico
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path
from typing import List, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Set environment variables
os.environ.setdefault("OPENROUTER_API_KEY", "test-api-key-replaced")
os.environ.setdefault("TESTING", "true")


def run_command(cmd: List[str], verbose: bool = False) -> int:
    """Run a command and return the exit code."""
    print(f"\n{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(cmd, capture_output=not verbose, text=True)
    
    if not verbose and result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    return result.returncode


def run_unit_tests(verbose: bool = False, coverage: bool = False) -> int:
    """Run unit tests only."""
    cmd = ["pytest", "tests/", "-v" if verbose else "-q", "-m", "unit"]
    
    if coverage:
        cmd.extend(["--cov=src", "--cov-report=term-missing"])
    
    return run_command(cmd, verbose)


def run_integration_tests(verbose: bool = False, real_api: bool = False) -> int:
    """Run integration tests."""
    cmd = ["pytest", "tests/", "-v" if verbose else "-q", "-m", "integration"]
    
    if not real_api:
        cmd.append("--skip-api")
    
    return run_command(cmd, verbose)


def run_all_tests(verbose: bool = False, coverage: bool = False) -> int:
    """Run all tests."""
    cmd = ["pytest", "tests/", "-v" if verbose else "-q"]
    
    if coverage:
        cmd.extend(["--cov=src", "--cov-report=term-missing", "--cov-report=html"])
    
    return run_command(cmd, verbose)


def run_specific_file(file_path: str, verbose: bool = False) -> int:
    """Run tests from a specific file."""
    cmd = ["pytest", file_path, "-v" if verbose else "-q", "-s"]
    return run_command(cmd, verbose)


def run_specific_test(test_name: str, verbose: bool = False) -> int:
    """Run a specific test by name."""
    cmd = ["pytest", "tests/", "-k", test_name, "-v" if verbose else "-q", "-s"]
    return run_command(cmd, verbose)


def run_quick_tests(verbose: bool = False) -> int:
    """Run quick tests (excluding slow and integration)."""
    cmd = ["pytest", "tests/", "-v" if verbose else "-q", "-m", "not slow and not integration"]
    return run_command(cmd, verbose)


def run_memory_tests(verbose: bool = False) -> int:
    """Run Memory VCS tests."""
    cmd = ["pytest", "tests/test_complex_integration_suite.py::TestMemoryVCS", "-v", "-s"]
    return run_command(cmd, verbose)


def run_iovba_tests(verbose: bool = False) -> int:
    """Run IOVBA Stack tests."""
    cmd = ["pytest", "tests/test_complex_integration_suite.py::TestStackIOVBA", "-v", "-s"]
    return run_command(cmd, verbose)


def run_ralph_tests(verbose: bool = False) -> int:
    """Run Ralph Loop tests."""
    cmd = ["pytest", "tests/test_complex_integration_suite.py::TestRalphLoop", "-v", "-s"]
    return run_command(cmd, verbose)


def run_rno_tests(verbose: bool = False) -> int:
    """Run RNO/LOCM tests."""
    cmd = ["pytest", "tests/test_complex_integration_suite.py::TestRNOLocom", "-v", "-s"]
    return run_command(cmd, verbose)


def run_ppcc_tests(verbose: bool = False) -> int:
    """Run PPCC Cycle tests."""
    cmd = ["pytest", "tests/test_complex_integration_suite.py::TestPPCCCycle", "-v", "-s"]
    return run_command(cmd, verbose)


def run_prompt_tests(verbose: bool = False) -> int:
    """Run complex prompts tests (requires API)."""
    cmd = ["pytest", "tests/test_complex_prompts.py", "-v", "-s", "-m", "integration"]
    return run_command(cmd, verbose)


def run_full_integration(verbose: bool = False) -> int:
    """Run full integration tests."""
    cmd = ["pytest", "tests/test_complex_integration_suite.py::TestFullIntegration", "-v", "-s", "-m", "integration"]
    return run_command(cmd, verbose)


def print_menu():
    """Print the interactive menu."""
    print("\n" + "="*60)
    print("OpenClaw Agent SaaS - Test Suite")
    print("="*60)
    print("\nOpciones:")
    print("  1. Todos los tests")
    print("  2. Tests unitarios")
    print("  3. Tests de integración")
    print("  4. Tests rápidos (sin slow/integration)")
    print("  5. Memory VCS tests")
    print("  6. IOVBA Stack tests")
    print("  7. Ralph Loop tests")
    print("  8. RNO/LOCM tests")
    print("  9. PPCC Cycle tests")
    print("  10. Complex Prompts tests (con API)")
    print("  11. Full Integration test")
    print("  12. Con cobertura")
    print("  0. Salir")
    print("="*60)


def interactive_mode():
    """Run in interactive mode."""
    while True:
        print_menu()
        choice = input("\nSelecciona una opción: ").strip()
        
        if choice == "0":
            print("Saliendo...")
            break
        elif choice == "1":
            run_all_tests(verbose=True)
        elif choice == "2":
            run_unit_tests(verbose=True)
        elif choice == "3":
            run_integration_tests(verbose=True)
        elif choice == "4":
            run_quick_tests(verbose=True)
        elif choice == "5":
            run_memory_tests(verbose=True)
        elif choice == "6":
            run_iovba_tests(verbose=True)
        elif choice == "7":
            run_ralph_tests(verbose=True)
        elif choice == "8":
            run_rno_tests(verbose=True)
        elif choice == "9":
            run_ppcc_tests(verbose=True)
        elif choice == "10":
            run_prompt_tests(verbose=True)
        elif choice == "11":
            run_full_integration(verbose=True)
        elif choice == "12":
            run_all_tests(verbose=True, coverage=True)
        else:
            print("Opción no válida")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="OpenClaw Agent SaaS Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python run_tests.py                     # Modo interactivo
  python run_tests.py --all               # Todos los tests
  python run_tests.py --unit              # Tests unitarios
  python run_tests.py --integration       # Tests de integración
  python run_tests.py --prompts           # Tests de prompts complejos
  python run_tests.py --file tests/x.py   # Archivo específico
  python run_tests.py -k "test_memory"    # Tests que coinciden
        """
    )
    
    # Test selection options
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--quick", action="store_true", help="Run quick tests")
    parser.add_argument("--prompts", action="store_true", help="Run complex prompts tests")
    parser.add_argument("--full", action="store_true", help="Run full integration test")
    
    # Specific modules
    parser.add_argument("--memory", action="store_true", help="Run Memory VCS tests")
    parser.add_argument("--iovba", action="store_true", help="Run IOVBA Stack tests")
    parser.add_argument("--ralph", action="store_true", help="Run Ralph Loop tests")
    parser.add_argument("--rno", action="store_true", help="Run RNO/LOCM tests")
    parser.add_argument("--ppcc", action="store_true", help="Run PPCC Cycle tests")
    
    # Execution options
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--file", type=str, help="Run tests from specific file")
    parser.add_argument("-k", type=str, help="Run tests matching pattern")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    
    args = parser.parse_args()
    
    # If no specific option, run interactive mode
    if len(sys.argv) == 1:
        interactive_mode()
        return
    
    # Run based on arguments
    exit_code = 0
    
    if args.all:
        exit_code = run_all_tests(verbose=args.verbose, coverage=args.coverage)
    elif args.unit:
        exit_code = run_unit_tests(verbose=args.verbose, coverage=args.coverage)
    elif args.integration:
        exit_code = run_integration_tests(verbose=args.verbose)
    elif args.quick:
        exit_code = run_quick_tests(verbose=args.verbose)
    elif args.prompts:
        exit_code = run_prompt_tests(verbose=args.verbose)
    elif args.full:
        exit_code = run_full_integration(verbose=args.verbose)
    elif args.memory:
        exit_code = run_memory_tests(verbose=args.verbose)
    elif args.iovba:
        exit_code = run_iovba_tests(verbose=args.verbose)
    elif args.ralph:
        exit_code = run_ralph_tests(verbose=args.verbose)
    elif args.rno:
        exit_code = run_rno_tests(verbose=args.verbose)
    elif args.ppcc:
        exit_code = run_ppcc_tests(verbose=args.verbose)
    elif args.file:
        exit_code = run_specific_file(args.file, verbose=args.verbose)
    elif args.k:
        exit_code = run_specific_test(args.k, verbose=args.verbose)
    elif args.interactive:
        interactive_mode()
    else:
        parser.print_help()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
