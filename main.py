"""Root entry point (shim). Prefer: sentinel-eval or python -m sentinel_eval.cli.main."""

from sentinel_eval.cli.main import main

if __name__ == "__main__":
    main()
