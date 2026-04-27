# Railway Deployment

This backend is the only part of the repo intended for Railway. The `laravel/` app is test-only and should not be deployed.

## Service Setup

1. Create a Railway project and add a service from this repository.
2. Set the service root directory to `/backend`.
3. Railway should detect [Dockerfile](/E:/Code/Projects/PNJCleaning/backend/Dockerfile:1) automatically.
4. The repo root includes [railway.toml](/E:/Code/Projects/PNJCleaning/railway.toml:1), which sets the Dockerfile builder, `/backend/**` watch path, and `/health` healthcheck.
5. In Networking, generate a Railway domain or attach your custom domain.

Railway's monorepo support and root-directory behavior are documented here:
https://docs.railway.com/guides/monorepo

If Railway does not automatically pick up the root config file for your service, set the service's Config as Code path to `/railway.toml` in the dashboard. Railway also supports custom config file paths such as `/backend/railway.toml`, but this repo uses a root-level config so it is auto-discoverable.

## Required Variables

Set these in the Railway service variables UI:

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SECRET_KEY`
- `PUBLIC_URL`

Set these as well if you want SSO enabled:

- `WORKOS_API_KEY`
- `WORKOS_CLIENT_ID`
- `WORKOS_REDIRECT_URI`

Recommended values:

- `PUBLIC_URL=https://<your-service-domain>`
- `WORKOS_REDIRECT_URI=https://<your-service-domain>/auth/callback`

## Runtime Notes

- The container now honors Railway's injected `PORT` variable in [Dockerfile](/E:/Code/Projects/PNJCleaning/backend/Dockerfile:24).
- A simple unauthenticated health endpoint is available at [app/main.py](/E:/Code/Projects/PNJCleaning/backend/app/main.py:29).
- This app uses Supabase directly, so Railway Postgres is not required unless you plan to redesign the data layer.
- Railway filesystem storage is ephemeral. Keep uploaded files in Supabase Storage, not on the container disk.

## Security

Before pushing this repo to a remote for Railway deployment, review and rotate any credentials that may already exist in local config or diagnostic files. At minimum, treat Supabase and WorkOS keys as compromised if they have ever been committed.
