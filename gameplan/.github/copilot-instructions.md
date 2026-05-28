---
description: 'Frappe Framework and VueJS 3 development standards and best practices'
applyTo: 'frontend/**/*.{vue,ts,js}, gameplan/**/*.py'
---

# Project Name: Gameplan

Gameplan is an async-first discussions tool for remote teams. It encourages thoughtful communication and deep-thinking.

Gameplan lets you start a discussion and have people comment on it at their own pace, encouraging thoughtful conversation
and deep thinking. No more feeling obligated to be online all the time.

Spaces help you categorize conversations by project, team, client, or topic – whatever makes sense for your team's workflow.
This keeps discussions tidy and easy to find.

# Gameplan: Tech Stack & Architecture

- **Backend**: Frappe Framework with Python
- **Frontend**: Vue 3 + TypeScript SPA with Vite dev server
- **Database**: MariaDB with structured doctypes
- **Search**: SQLite FTS5 for full-text search capabilities
- **Real-time**: WebSockets via Socket.IO for live updates
- **UI Library**: frappe-ui (local copy in `./frappe-ui/`)

## Key Architecture Patterns

**Dual App Structure**: Gameplan runs as a Frappe app with a Vue SPA frontend served at `/g` route via `gameplan/www/g.py`

**DocType-Driven Backend**: Core entities like `GP Discussion`, `GP Comment`, `GP Project`, `GP Team` follow Frappe's DocType pattern in `gameplan/gameplan/doctype/`

**Vite Integration**: Frontend uses frappe-ui's Vite plugin for proxy setup, type generation, and build optimization - see `frontend/vite.config.js`

**Routing**: Vue Router handles client-side routing under `/g/` with complex nested layouts (Team → Project → Space hierarchy)

# Frontend: VueJS 3 Development Instructions

Instructions for building high-quality VueJS 3 applications with the Composition API, TypeScript, and modern best practices.

## Frontend Project Context
- `./frontend/` is the main directory for VueJS frontend code
- Vue 3.x with Composition API as default
- TypeScript for type safety
- Single File Components (`.vue`) with `<script setup lang="ts">` syntax
- Vite as the build tool
- We don't use any state management libraries
- Official Vue style guide and best practices
- frappe-ui for UI components and data fetching utilities
- The folder `./frappe-ui/` is a local copy of the frappe-ui library, look through it to check what components are available to use.

## Frontend Project Structure
- `./frontend/src/` contains the main source code
- `./frontend/src/components/` for reusable components
- `./frontend/src/pages/` for page components
- `./frontend/src/data/` for data fetching composables
- `./frontend/src/utils/` for utility functions and helpers
- `./frontend/src/directives/` for custom directives

## Vite dev server
- Assume the Vite dev server is already running on port 8080
- Use `http://gameplan.frappe.test:8080/g` to access the frontend during development

## Critical Integration Points

**Frontend-Backend Bridge**:
- App entry point: `gameplan/www/g.py` serves the Vue SPA and handles boot data
- Backend API endpoints exposed through `gameplan/api.py` with `@frappe.whitelist()` decorators
- Real-time updates via Socket.IO configured in frontend `socket.js`

**Local frappe-ui Development**:
- Local frappe-ui copy in `./frappe-ui/` for development
- Vite config automatically aliases to local version in dev mode
- TipTap package conflicts resolved via dynamic aliasing in `vite.config.js`

**Route Structure**:
- Vue Router base path: `/g/` with nested team/project/space hierarchy
- Legacy team/project routes redirect to unified spaces pattern
- Complex nested layouts: Team → Project → Space with shared components

## Development Standards

### Architecture
- Favor the Composition API (`setup` functions and composables) over the Options API
- Organize components and composables by feature or domain for scalability
- Separate UI-focused components (presentational) from logic-focused components (containers)
- Put page components in a `./frontend/src/pages/` directory
- Use a `./frontend/src/components/` directory for shared UI components
- For small components, just put them in one file `pages/Page.vue` or `./frontend/src/components/Component.vue`
- For larger components, split it into smaller components and composables and put them in a folder named after the component and include an `index.ts` (e.g., `./frontend/src/components/MyComponent/index.ts`, `pages/MyPage/index.ts`)

### TypeScript Integration
- Enable `strict` mode in `tsconfig.json` for maximum type safety
- Use `defineComponent` or `<script setup lang="ts">` with `defineProps` and `defineEmits`
- Leverage `PropType<T>` for typed props and default values
- Use interfaces or type aliases for complex prop and state shapes
- Define types for event handlers, refs, and `useRoute`/`useRouter` hooks
- Implement generic components and composables where applicable

### Component Design
- Adhere to the single responsibility principle for components
- Use PascalCase for component names and for file names
- Keep components small and focused on one concern
- Use `<script setup lang="ts">` syntax for brevity and performance
- Validate props with TypeScript; use runtime checks only when necessary
- Favor slots and scoped slots for flexible composition
- Prefer `useTemplateRef` for accessing DOM elements instead of `ref` or `querySelector` in `setup`

### State Management
- Don't use any state management libraries like Vuex or Pinia
- For simple local state, use `ref` and `reactive` within `setup`
- Use `computed` for derived state
- Keep state normalized for complex structures

### Composition API Patterns
- Create reusable composables for shared logic, e.g., `useFetch`, `useAuth`
- Use `watch` and `watchEffect` with precise dependency lists
- Cleanup side effects in `onUnmounted` or `watch` cleanup callbacks
- Use `provide`/`inject` sparingly for deep dependency injection

### Styling
- Always prefer tailwindcss for styling
- Use utility classes for layout and spacing
- Use semantic class names wherever possible:
  - Background color classes: `bg-surface-white`, `bg-surface-gray-1`, `bg-surface-gray-2`, ..., `bg-surface-gray-9`, `bg-surface-black`
  - Text color classes: `text-ink-white`, `text-ink-gray-1`, `text-ink-gray-2`, ..., `text-ink-gray-9`, `text-ink-black`
  - Fill color classes: `fill-ink-*`
  - Placeholder color classes: `placeholder-ink-*`
  - Border color classes: `border-outline-white`, `border-outline-gray-1`, `border-outline-gray-2`, ..., `border-outline-gray-5`, `border-outline-black`
  - Ring color classes: `ring-outline-*`
  - Divide color classes: `divide-ink-gray-*`
  - Font size classes: `text-xs`, `text-sm`, `text-base`, `text-lg`, `text-xl`, `text-2xl`, `text-3xl`
  - Font size for multiline text: `text-p-xs`, `text-p-sm`, `text-p-base`, `text-p-lg`, `text-p-xl`, `text-p-2xl`
- Always use gray shades for everything, never use color shades even for primary states
- Other than these, use standard Tailwind CSS classes for everything else
- Sparingly use `<style scoped>` when necessary
- Implement mobile-first, responsive design with CSS Grid and Flexbox
- Ensure styles are accessible (contrast, focus states)

### Performance Optimization
- Apply `v-once` and `v-memo` for static or infrequently changing elements
- Avoid unnecessary watchers; prefer `computed` where possible
- Tree-shake unused code and leverage Vite’s optimization features

### Data Fetching
- Use `useDoc`, `useList`, and `useCall` from frappe-ui for data fetching
- Look at `./frontend/src/data/` for examples of data fetching composables
- Handle loading, error, and success states explicitly

When working with a list of documents, use the `useList` composable:
```ts
const items = useList<Doctype>({
  doctype: 'My Doctype',
  filters: () => ({ field: 'value' }),
  fields: ['name', 'title', 'modified'],
  limit: 10,
  cacheKey: 'my-doctype-list',
  immediate: true,
})
// update fields in a single row based on its name
items.setValue.submit({ name: '<id>', title: 'Item Title' }) // items.setValue.loading, items.setValue.error
// add a new item
items.insert.submit({ title: 'New Item' })
// delete an item
items.delete.submit({ name: '<id>' })
```

When working with a single document, use the `useDoc` composable:
```ts
const item = useDoc<Doctype>({
  doctype: 'My Doctype',
  name: '<id>',
  methods: {
    customMethod: 'custom_method', // custom_method is a server-side whitelisted class method in my_doctype.py
  }
})

item.doc.title // access fields
item.setValue.submit({ title: 'Updated Title' }) // update fields
item.delete.submit() // delete the document
item.customMethod.submit({ param: 'value' }) // call custom method
```

### Icons

- Always use lucide icons for consistency
- Never use FeatherIcon component (it is deprecated)
- To use a lucide icon, directly add the component in the template, no need to import it in the script section:
  ```vue
  <template>
    <LucideIconName class="size-4" />
  </template>
  ```
- To use a lucide icon in the script section, import it like this, ignore any typescript errors related to lucide icons:
  ```ts
  import LucideIconName from '~icons/lucide/icon-name'
  ```

## Utilities and Composables

- @vueuse/core is installed in this project
- If there is a scenario where a vueuse composable can simplify the code, prefer using it over custom implementations
- Common composables include `useLocalStorage`, `useDebounce`, `useElementSize`
- Never use `useFetch`, always use `useList`, `useDoc`, `useCall` for data fetching from frappe-ui

### Error Handling
- Use global error handler (`app.config.errorHandler`) for uncaught errors
- Wrap risky logic in `try/catch`; provide user-friendly messages
- Use `errorCaptured` hook in components for local boundaries
- Display fallback UI or error alerts gracefully

### Forms and Validation
- Build forms with controlled `v-model` bindings
- Validate on blur or input with debouncing for performance
- Handle file uploads and complex multi-step forms in composables
- Ensure accessible labeling, error announcements, and focus management

### Routing
- Use Vue Router 4 with `createRouter` and `createWebHistory`
- Implement nested routes and route-level code splitting
- Protect routes with navigation guards (`beforeEnter`, `beforeEach`)
- Use `useRoute` and `useRouter` in `setup` for programmatic navigation
- Manage query params and dynamic segments properly


### Security
- Avoid using `v-html`; sanitize any HTML inputs rigorously
- Use CSP headers to mitigate XSS and injection attacks
- Validate and escape data in templates and directives
- Store sensitive tokens in HTTP-only cookies, not `localStorage`

### Accessibility
- Use semantic HTML elements and ARIA attributes
- Manage focus for modals and dynamic content
- Provide keyboard navigation for interactive components
- Add meaningful `alt` text for images and icons
- Ensure color contrast meets WCAG AA standards

## Implementation Process
1. Plan component and composable architecture
3. Create core UI components and layout
5. Implement data fetching and state logic
10. Ensure accessibility compliance

## Additional Guidelines
- Follow Vue’s official style guide (vuejs.org/style-guide)
- Use ESLint (with `plugin:vue/vue3-recommended`) and Prettier for code consistency
- Write meaningful commit messages and maintain clean git history
- Keep dependencies up to date and audit for vulnerabilities
- Document complex logic with JSDoc/TSDoc
- Use Vue DevTools for debugging and profiling

## Common Patterns
- Renderless components and scoped slots for flexible UI
- Compound components using provide/inject
- Custom directives for cross-cutting concerns

# Backend: Frappe Framework Development Instructions

## Backend Project Context
- Frappe Framework is a full-stack web application framework that contains all the necessary components for building modern web applications.
- It provides background workers using Redis, real-time updates using sockets, database using MariaDB.
- Bench is the official command-line tool for managing Frappe applications.

## Backend project structure
- `./gameplan/` is the main directory for backend code
- `./gameplan/gameplan/` contains the main doctypes and business logic
- `./gameplan/gameplan/doctype/` contains individual doctype definitions
- `./gameplan/api.py` contains some API endpoints and logic

## Critical Development Workflows

**Local Development Setup**:
- Backend runs via `bench start` from `frappe-bench` directory
- Frontend dev server: `cd frontend && yarn dev` (runs on port 8080)
- Access app at `http://gameplan.frappe.test:8080/g` during development
- Site-specific commands: `bench --site gameplan.frappe.test <command>`

**Data Query Patterns**:
- Always prefer `frappe.qb.get_query()` over `frappe.db.get_all()` for new code
- Use `frappe.qb.get_query(..., ignore_permissions=False)` when permission checks are needed
- See examples in `gameplan/api.py` for proper query builder usage

**Debugging Workflow**:
- Create debug files like `./gameplan/debug.py` with `def execute():` function
- Run with `bench --site gameplan.frappe.test execute gameplan.debug.execute`
- Use `print()` statements for console output during debugging

**Search Integration**:
- Full-text search powered by Redisearch via `sqlite_search` hook in `hooks.py`
- Search implementation in `gameplan.search_sqlite.GameplanSearch`

## DocType Architecture Patterns

**Core Entity Structure**:
- `GP Project` - Referred to as "Spaces" in the UI. Every discussion, task, and page belongs to a space (GP Project).
- `GP Team` - Referred to as "Category" in the UI. Every project belongs to a team.
- `GP Discussion` - Main discussion threads
- `GP Comment` - Threaded comments with reactions. A discussion can have multiple comments.
- `GP Page` - Collaborative documents
- `GP Task` - Task management with assignees
- `GP User Profile` - Extended user information

**Permission System**:
- Custom permission logic in `has_permission` hooks (see `hooks.py`)
- Example: `GP Page` permissions in `gameplan.gameplan.doctype.gp_page.gp_page.has_permission`
- Team/project membership controls access to discussions and pages

**Auto-generated Types**:
- TypeScript types generated via frappe-ui's `frappeTypes` plugin configuration
- See `frontend/vite.config.js` for doctype list that generates frontend types

## Miscellaneous

- Ignore newline errors in all files

## Code Comments

- Only add comments that explain why something is done, not what is done
- Use JSDoc/TSDoc for documenting complex functions, components, and composables
- Don't add unnecessary comments for simple code
- Use inline comments sparingly, only when the code is not self-explanatory
