# PowerShell script to run PostgreSQL with Pgvector in a Docker container

# Set environment variables
$env:POSTGRES_DB = "ai"
$env:POSTGRES_USER = "ai"
$env:POSTGRES_PASSWORD = "ai"
$env:PGDATA = "/var/lib/postgresql/data/pgdata"

# Run the Docker container
docker run -d `
  -e POSTGRES_DB=$env:POSTGRES_DB `
  -e POSTGRES_USER=$env:POSTGRES_USER `
  -e POSTGRES_PASSWORD=$env:POSTGRES_PASSWORD `
  -e PGDATA=$env:PGDATA `
  -v pgvolume:/var/lib/postgresql/data `
  -p 5532:5432 `
  --name pgvector `
  phidata/pgvector:16
