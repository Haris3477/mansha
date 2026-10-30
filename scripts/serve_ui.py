"""Serve Mansha locally: python -m scripts.serve_ui [--fake] [--port 8000]."""

import argparse

import uvicorn

from mansha.web.app import create_app

HOST = "127.0.0.1"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Serve the local Mansha UI.")
    parser.add_argument("--fake", action="store_true", help="Use offline sample replies.")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)
    print(f"Mansha: http://{HOST}:{args.port}", flush=True)
    uvicorn.run(create_app(fake=args.fake), host=HOST, port=args.port,
                timeout_graceful_shutdown=3)


if __name__ == "__main__":
    main()
