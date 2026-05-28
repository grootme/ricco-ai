<div align="center" markdown="1">

<img src="./frontend/public/gameplan-logo.svg" alt="Gameplan logo" width="80" />
<h1>Gameplan</h1>

**Open Source Discussions Platform for Remote Teams**

<a href="https://dashboard.cypress.io/projects/y2q697/runs">
    <img alt="cypress" src="https://img.shields.io/endpoint?url=https://dashboard.cypress.io/badge/simple/y2q697/main&style=flat&logo=cypress">
</a>



<div>
    <picture>
        <source media="(prefers-color-scheme: dark)" srcset=".github/assets/gameplan-hero-dark.png">
        <img width="1402" alt="Gameplan Homescreen Screenshot" src=".github/assets/gameplan-hero-light.png">
    </picture>
</div>

</div>

## Gameplan

Gameplan is an async-first discussions tool for remote teams. It encourages thoughtful communication and deep-thinking.

### Motivation
We've been remote first since day one, but as our team grew, chat tools like Telegram fell short. Missing out on crucial conversations became a major issue. We needed a better way to keep everyone connected and in sync. That's how Gameplan was born - to solve the problems of modern remote work!

### Key Features
- **Thread-first discussions**: Gameplan lets you start a discussion and have people comment on it at their own pace, encouraging thoughtful conversation and deep thinking. No more feeling obligated to be online all the time.

- **Spaces for organization**: Spaces help you categorize conversations by project, team, client, or topic – whatever makes sense for your team's workflow. This keeps discussions tidy and easy to find.

- **Customizable profiles**: Get a better picture of who's on your team with profiles that let everyone showcase their personality: cover images, short bios, and profile pictures.

- **Pages for note-taking**: Use pages as digital notes to jot down meeting minutes, proposals, ideas – whatever sparks creativity! They can be private by default or shared with just your team or specific spaces.

### Under the Hood

- [Frappe Framework](https://github.com/frappe/frappe): A full-stack batteries-included web framework.
- [Frappe UI](https://github.com/frappe/frappe-ui): A Vue UI library for a modern user interface built on our [design system](https://www.figma.com/community/file/1407648399328528443).
- [Redisearch](https://github.com/RediSearch/RediSearch): A powerful search and indexing engine built on top of Redis.

## Production setup
### Managed Hosting

You can try [Frappe Cloud](https://frappecloud.com), a simple, user-friendly and sophisticated [open-source](https://github.com/frappe/press) platform to host Frappe applications.

It takes care of installation, setup, upgrades, monitoring, maintenance and support of your Frappe deployments. It is a fully featured developer platform with an ability to manage and control multiple Frappe deployments.

<div>
	<a href="https://frappecloud.com/gameplan/signup" target="_blank">
		<picture>
			<source media="(prefers-color-scheme: dark)" srcset="https://frappe.io/files/try-on-fc-white.png">
			<img src="https://frappe.io/files/try-on-fc-black.png" alt="Try on Frappe Cloud" height="28" />
		</picture>
	</a>
</div>

## Development setup
### Docker
You need Docker, docker-compose and git setup on your machine. Refer [Docker documentation](https://docs.docker.com/). After that, run the following commands:
```
git clone https://github.com/frappe/gameplan
cd gameplan/docker
docker-compose up
```

Wait for sometime until the setup script creates a site. After that you can
access `http://localhost:8000` in your browser and Gameplan's login screen
should show up.

Use the following credentials to log in:

- Username: `alex@example.com`
- Password: `123`

### Local Development (without Docker)

This app depends on the `develop` branch of [frappe](https://github.com/frappe/frappe).

#### Prerequisites
- Frappe-bench set up locally ([installation guide](https://frappeframework.com/docs/v14/user/en/installation))
- Node.js and yarn
- The local frappe-ui copy is included in `./frappe-ui/` for development

#### Step 1: Set up the Backend

1. In your frappe-bench directory, run the following commands in separate terminal sessions:
    ```sh
    # Terminal 1 - Start the Frappe server
    cd frappe-bench
    bench start
    ```

2. Open a new terminal session for the remaining setup:
    ```sh
    cd frappe-bench
    bench new-site gameplan.test
    bench get-app gameplan
    bench --site gameplan.test install-app gameplan
    bench --site gameplan.test add-to-hosts
    bench --site gameplan.test browse --user Administrator
    ```

#### Step 2: Set up the Frontend

1. Open a new terminal session and navigate to the gameplan app:
    ```sh
    cd frappe-bench/apps/gameplan
    ```

2. Initialize and update the frappe-ui submodule (required):
    ```sh
    # If frappe-ui is not initialized
    git submodule init
    git submodule update

    # To pull the latest version of frappe-ui
    git submodule update --remote
    ```

3. Install frontend dependencies:
    ```sh
    yarn install
    ```

4. **Optional: For local frappe-ui development**, install frappe-ui dependencies (use `yarn` in frappe-ui):
    ```sh
    cd frappe-ui
    yarn install
    cd ..
    ```

5. Start the Vite development server:
    ```sh
    yarn dev
    ```

6. Access the application at `http://gameplan.test:8080/g`

#### How Local Vite Aliasing Works

Gameplan uses a custom Vite configuration to support local development with a bundled copy of frappe-ui. Here's how it works:

- The `./frappe-ui/` directory is a local copy of the frappe-ui library bundled with Gameplan
- During development (`vite dev`), Vite automatically detects if local frappe-ui dependencies are installed
- If they are installed, Vite aliases all imports of `frappe-ui` to use the local copy instead of the npm package

**Alias Configuration**:
The Vite config (`frontend/vite.config.js`) implements smart aliasing:

```javascript
// Development mode: Uses local frappe-ui if node_modules exist
const useLocalFrappeUI = isDev && existsSync(path.join(localFrappeUIPath, 'node_modules'))

// CSS must be aliased before the general module alias
const localFrappeUIAliases = useLocalFrappeUI ? {
  'frappe-ui/style.css': path.resolve(localFrappeUIPath, 'src', 'style.css'),
  'frappe-ui': localFrappeUIPath,
} : {}
```

**Dependency Resolution**:
- TipTap packages are specially handled to resolve from the local frappe-ui's `node_modules` when using the local copy
- This prevents version conflicts between frappe-ui and gameplan dependencies
- The config automatically falls back to the npm package if local frappe-ui is not available

**When to Install frappe-ui Dependencies**:
- Only needed if you're modifying frappe-ui components or contributing to frappe-ui development
- Use `yarn install` in the `frappe-ui` directory
- For normal Gameplan development, the npm package version will be used automatically
- If you see a warning about frappe-ui dependencies not being installed, run `cd frappe-ui && yarn install` only if you need local development

**Contributing to frappe-ui**:
- The `frappe-ui` directory is a Git submodule pointing to the [frappe/frappe-ui](https://github.com/frappe/frappe-ui) repository
- If you make changes to frappe-ui, you must submit them as a separate Pull Request to the [frappe-ui repository](https://github.com/frappe/frappe-ui)
- Changes to frappe-ui submodule commits in Gameplan are intentionally not committed to keep the submodule independently versioned
- Test your frappe-ui changes locally with Gameplan before submitting a PR

#### Frontend Development Environment

- **Vite Dev Server**: Runs on port 8080 by default
- **Frappe Proxy**: Automatically proxies API requests to the backend via `frappeProxy` plugin
- **Type Generation**: TypeScript types are auto-generated from backend doctypes
- **Access URL**: `http://gameplan.test:8080/g`

#### Backend and Frontend Workflow

- Backend runs on `http://gameplan.test:8000` via `bench start`
- Frontend dev server runs on `http://gameplan.test:8080` and proxies API calls to the backend
- The Vite dev server uses HMR (Hot Module Replacement) for instant code updates
- Both must be running simultaneously for local development

## Links

- [Discuss Gameplan](https://github.com/frappe/gameplan/discussions)

<br>
<br>
<div align="center">
	<a href="https://frappe.io" target="_blank">
		<picture>
			<source media="(prefers-color-scheme: dark)" srcset="https://frappe.io/files/Frappe-white.png">
			<img src="https://frappe.io/files/Frappe-black.png" alt="Frappe Technologies" height="28"/>
		</picture>
	</a>
</div>
