# Authentication Guide

## GitHub OAuth (Device Flow)
- Uses GitHub's OAuth 2.0 Device Flow (`https://github.com/login/device/code`).
- No confidential `client_secret` is embedded in the repository.
- You only provide a public OAuth App `client_id` (via prompt, `settings`, or `GITHUB_OAUTH_CLIENT_ID`).

## Personal Access Token (PAT)
- Input is masked (`password=True`) and never echoed or logged.
- Minimum scopes:
  - `read:user`: Required for profile and contribution calendar retrieval.
  - `repo`: Required only for creating or pushing to repositories.
