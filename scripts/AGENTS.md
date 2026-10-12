# Scripts

Build the Docker image and run it as a container named `pm` on port 8000, with `.env` passed in and `./data` mounted at `/app/data`.

- Mac/Linux: `scripts/start.sh`, `scripts/stop.sh`
- Windows: `scripts/start.ps1`, `scripts/stop.ps1`

Start rebuilds the image and replaces any running `pm` container. Stop removes the container; data in `./data` is kept.
