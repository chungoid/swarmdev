# SwarmDev MCP Servers - Stable Packaging from github.com/chungoid/swarmdev-mcp-servers

This repository contains stable Docker-packaged versions of the official [Model Context Protocol (MCP) servers](https://github.com/modelcontextprotocol/servers) for use with SwarmDev.

## Why This Repository Exists

SwarmDev requires stable, versioned MCP server implementations that won't change unexpectedly. This repository:

- **Packages official MCP servers** from the [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) repository
- **Provides stable Docker images** published to GitHub Container Registry (GHCR)  
- **Ensures version consistency** for SwarmDev deployments
- **Maintains compatibility** even if upstream servers change

## Available Servers

All 7 reference MCP servers are packaged and available:

| Server | Language | Description | Docker Image |
|--------|----------|-------------|--------------|
| **everything** | TypeScript | Reference/test server with prompts, resources, and tools | `ghcr.io/chungoid/everything:latest` |
| **fetch** | Python | Web content fetching and conversion for efficient LLM usage | `ghcr.io/chungoid/fetch:latest` |
| **filesystem** | TypeScript | Secure file operations with configurable access controls | `ghcr.io/chungoid/filesystem:latest` |
| **git** | Python | Tools to read, search, and manipulate Git repositories | `ghcr.io/chungoid/git:latest` |
| **memory** | TypeScript | Knowledge graph-based persistent memory system | `ghcr.io/chungoid/memory:latest` |
| **sequentialthinking** | TypeScript | Dynamic and reflective problem-solving through thought sequences | `ghcr.io/chungoid/sequentialthinking:latest` |
| **time** | Python | Time zone operations and conversions | `ghcr.io/chungoid/time:latest` |

## Docker Image Tags

Each server is available with multiple tags:

- `latest` - Latest build from main branch
- `stable-YYYYMMDD-HHMMSS` - Timestamped stable releases  
- `stable-v*` - Semantic version releases for stable tags
- `main` - Latest main branch build

## Usage with SwarmDev

These images are automatically configured in SwarmDev. The SwarmDev `pull-images` command will download all required images:

```bash
swarmdev pull-images
```

This command automatically pulls:
```bash
docker pull ghcr.io/chungoid/everything:latest
docker pull ghcr.io/chungoid/fetch:latest  
docker pull ghcr.io/chungoid/filesystem:latest
docker pull ghcr.io/chungoid/git:latest
docker pull ghcr.io/chungoid/memory:latest
docker pull ghcr.io/chungoid/sequentialthinking:latest
docker pull ghcr.io/chungoid/time:latest
```

## Manual Usage

Each server can be run individually for testing:

```bash
# Example: Git server with repository access
docker run -i --rm -v $(pwd):/workspace ghcr.io/chungoid/git:latest

# Example: Memory server  
docker run -i --rm ghcr.io/chungoid/memory:latest

# Example: Fetch server
docker run -i --rm ghcr.io/chungoid/fetch:latest
```

## Build and Release Process

### Automatic Builds

Images are automatically built and published via GitHub Actions when:
- Code is pushed to `main` branch 
- Tags matching `stable-v*` are created
- Manual workflow dispatch is triggered

### Multi-Platform Support

All images are built for:
- `linux/amd64` (Intel/AMD x64)
- `linux/arm64` (Apple Silicon, ARM64)

### Creating Stable Releases

To create a new stable release:

```bash
# Tag a stable version
git tag stable-v1.0.0
git push origin stable-v1.0.0
```

This triggers builds with tags like:
- `ghcr.io/chungoid/git:stable-v1.0.0`
- `ghcr.io/chungoid/git:stable-1.0.0` 
- `ghcr.io/chungoid/git:latest`

## Source Code

This repository contains **unmodified source code** from the official [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) repository. 

The only additions are:
- GitHub Actions workflow for Docker builds (`/.github/workflows/docker-build.yml`)
- This documentation (`/SWARMDEV-README.md`)
- Stable versioning and packaging infrastructure

## Upstream Synchronization  

To update with the latest upstream changes:

```bash
git fetch upstream
git merge upstream/main
git push origin main  # Triggers new builds automatically
```

## Integration with SwarmDev

SwarmDev's MCP configuration automatically references these stable images:

```json
{
  "servers": {
    "git": {
      "command": ["docker", "run", "--rm", "-i", "ghcr.io/chungoid/git:latest"],
      "timeout": 30,
      "enabled": true
    },
    "memory": {
      "command": ["docker", "run", "--rm", "-i", "ghcr.io/chungoid/memory:latest"], 
      "timeout": 30,
      "enabled": true
    }
  }
}
```

See the [SwarmDev repository](https://github.com/chungoid/swarmdev) for complete configuration details.

## License

This project maintains the same MIT license as the original MCP servers repository.

## Links

- **Official MCP Servers**: https://github.com/modelcontextprotocol/servers
- **SwarmDev**: https://github.com/chungoid/swarmdev  
- **Model Context Protocol**: https://modelcontextprotocol.io/
- **Docker Images**: https://github.com/chungoid/swarmdev-mcp-servers/pkgs/container/

## Support

For issues with:
- **Docker packaging**: Open an issue in this repository
- **MCP server functionality**: Check the [official MCP servers repository](https://github.com/modelcontextprotocol/servers/issues)
- **SwarmDev integration**: Check the [SwarmDev repository](https://github.com/chungoid/swarmdev/issues) 