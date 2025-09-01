# FirstRead Web Application

A modern Next.js web application with NextAuth.js authentication.

## Features

- **User Authentication**: Secure login and registration using NextAuth.js
- **Modern UI**: Beautiful, responsive design with Tailwind CSS
- **Server Actions**: Form handling with Next.js server actions
- **Protected Routes**: Middleware-based route protection
- **Dark Mode Support**: Automatic dark/light theme switching
- **TypeScript**: Full TypeScript support for better development experience

## Authentication Flow

### Registration
1. User visits `/register` page
2. Fills out email and password form
3. Form submits to backend API endpoint `/users/register`
4. On successful registration, user is automatically signed in
5. Redirected to home page (`/`)

### Login
1. User visits `/login` page
2. Enters email and password
3. Form submits to NextAuth.js credentials provider
4. Backend validates credentials at `/users/login`
5. On successful login, user is redirected to home page (`/`)

### Logout
1. User clicks "Sign Out" button
2. NextAuth.js handles the logout process
3. User is redirected to home page

## Environment Variables

Create a `.env.local` file in the `apps/web` directory:

```env
NEXTAUTH_SECRET=your-secret-key-here
NEXTAUTH_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## Project Structure

```
src/
├── app/                    # Next.js app directory
│   ├── (auth)/            # Authentication route group
│   │   ├── login/         # Login page
│   │   └── register/      # Registration page
│   ├── api/               # API routes
│   │   └── auth/          # Authentication API routes
│   ├── globals.css        # Global styles
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Home page
├── auth.ts                # NextAuth.js configuration
├── components/            # Reusable components
│   ├── ui/                # UI components (Button, Input, Card, etc.)
│   └── navigation.tsx     # Navigation component
├── lib/                   # Utility functions
│   ├── auth-actions.ts    # Server actions for authentication
│   └── utils.ts           # General utility functions
└── middleware.ts          # Next.js middleware for route protection
```

## Backend Integration

The application expects a backend API with the following endpoints:

- `POST /users/register` - User registration
- `POST /users/login` - User authentication

Both endpoints should return an `access_token` on success.

## Styling

The application uses Tailwind CSS with custom CSS variables for theming. The design includes:

- Gradient backgrounds
- Glassmorphism effects
- Responsive design
- Dark mode support
- Smooth animations and transitions

## Security Features

- CSRF protection with NextAuth.js
- Secure password handling
- Protected routes with middleware
- Server-side form validation
- Secure session management
