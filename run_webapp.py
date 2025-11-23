#!/usr/bin/env python3
"""Run the Fisher web application."""

import sys
import argparse
from fisher.webapp import run_webapp

def main():
    parser = argparse.ArgumentParser(description='Run Fisher Web Application')
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Host to bind to (default: 127.0.0.1)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to bind to (default: 5000)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Run in debug mode'
    )

    args = parser.parse_args()

    print(f"Starting Fisher Web Application...")
    print(f"Server running at: http://{args.host}:{args.port}")
    print(f"Press CTRL+C to stop the server\n")

    try:
        run_webapp(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")
        sys.exit(0)

if __name__ == '__main__':
    main()
