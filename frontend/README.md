# Cookidoo Agent Assistant - Frontend

React TypeScript frontend for the Cookidoo Agent Assistant application.

## Features

- 🍳 **Recipe Browsing & Search**: Search and browse Cookidoo recipes
- ✨ **AI-Powered Modifications**: Modify recipes using natural language
- 💬 **Chat Assistant**: Ask cooking questions and get AI-powered answers
- 🛒 **Smart Shopping Lists**: Generate consolidated shopping lists from multiple recipes
- 📱 **Responsive Design**: Material-UI components optimized for all screen sizes

## Tech Stack

- **Framework**: React 18 with TypeScript
- **UI Library**: Material-UI (MUI) v5
- **Routing**: React Router v6
- **State Management**: React Query for server state
- **HTTP Client**: Axios
- **Styling**: Emotion (CSS-in-JS)

## Prerequisites

- Node.js 16+ and npm/yarn
- Backend API running on port 8000 (or configure via env)

## Getting Started

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_MCP_URL=http://localhost:8001
```

### 3. Run Development Server

```bash
npm start
```

The app will open at http://localhost:3000

### 4. Build for Production

```bash
npm run build
```

The optimized build will be in the `build/` directory.

## Project Structure

```
frontend/
├── public/              # Static files
├── src/
│   ├── components/      # Reusable React components
│   │   └── Layout.tsx   # Main layout with navigation
│   ├── pages/          # Page components
│   │   ├── HomePage.tsx
│   │   ├── RecipesPage.tsx
│   │   ├── ChatPage.tsx
│   │   └── ShoppingListPage.tsx
│   ├── services/       # API clients and services
│   │   └── api.ts      # Axios API client
│   ├── types/          # TypeScript interfaces
│   │   ├── recipe.ts
│   │   ├── chat.ts
│   │   ├── shopping.ts
│   │   └── api.ts
│   ├── App.tsx         # Main app component
│   ├── index.tsx       # Entry point
│   └── index.css       # Global styles
├── package.json
├── tsconfig.json       # TypeScript configuration
└── .env.example        # Environment template
```

## Available Scripts

- `npm start` - Run development server (port 3000)
- `npm build` - Build production bundle
- `npm test` - Run tests
- `npm run lint` - Lint code
- `npm run format` - Format code with Prettier

## API Integration

The frontend communicates with the FastAPI backend through the axios client in `src/services/api.ts`.

### Example Usage

```typescript
import { recipeApi } from './services/api';

// Search recipes
const results = await recipeApi.searchRecipes('vegan pasta', {
  dietary_restrictions: ['vegan'],
  max_prep_time_minutes: 30
});

// Modify recipe
const modified = await recipeApi.modifyRecipe({
  recipe_id: 'recipe-123',
  modifications: 'Make it gluten-free and double the servings'
});
```

## Docker Deployment

The frontend is containerized using a multi-stage Docker build with nginx.

```bash
# Build image
docker build -f docker/frontend.Dockerfile -t cookidoo-frontend .

# Run container
docker run -p 3000:80 cookidoo-frontend
```

Or use docker-compose from the root directory:

```bash
docker-compose up frontend
```

## Development Guidelines

- Follow TypeScript strict mode
- Use functional components with hooks
- Leverage Material-UI's sx prop for styling
- Implement proper error handling with try-catch
- Use React Query for API data fetching and caching
- Keep components small and focused
- Write unit tests for complex logic

## Environment Variables

| Variable            | Description      | Default                  |
| ------------------- | ---------------- | ------------------------ |
| `REACT_APP_API_URL` | Backend API URL  | `http://localhost:8000`  |
| `REACT_APP_MCP_URL` | MCP Server URL   | `http://localhost:8001`  |
| `REACT_APP_NAME`    | Application name | `Cookidoo Agent Assistant` |
| `REACT_APP_VERSION` | App version      | `1.0.0`                  |

## Future Enhancements

- [ ] Implement full recipe modification UI with form
- [ ] Add recipe image upload and preview
- [ ] Implement user authentication
- [ ] Add recipe favorites and collections
- [ ] Implement offline support with PWA
- [ ] Add voice input for hands-free cooking
- [ ] Implement meal planning calendar
- [ ] Add nutritional analysis charts

## Contributing

1. Follow the coding guidelines in the project root
2. Write tests for new features
3. Use conventional commits for commit messages
4. Run linter before committing: `npm run lint`

## License

Part of the Cookidoo Agent Assistant project.
