# Frontend Components

This directory contains the React components for the Contextual URL Shortener frontend application.

## Component Overview

### Core Components

#### LinkCreator
The main component for creating short links with the following features:
- URL input with validation
- Domain selection (go2.video, go2.reviews, go2.tools)
- Real-time custom code availability checking
- Password protection option
- Expiration date setting
- Responsive design with Tailwind CSS
- Accessibility compliance (ARIA labels, keyboard navigation)

**Props:**
- `onLinkCreated?: (link: CreateLinkResponse) => void` - Callback when link is created

#### LinkDisplay
Component for displaying created short links with:
- Copy to clipboard functionality
- QR code preview
- Link details display
- Analytics navigation
- Mobile-responsive layout

**Props:**
- `link: CreateLinkResponse` - The created link data
- `showAnalytics?: boolean` - Whether to show analytics button
- `onViewAnalytics?: (code: string) => void` - Analytics callback

#### AnalyticsDashboard
Comprehensive analytics dashboard featuring:
- Time-series click charts using Recharts
- Geographic distribution with pie charts
- Device and referrer breakdowns
- Export functionality (CSV/JSON)
- Real-time data refresh
- Mobile-responsive grid layout

**Props:**
- `code: string` - Link code to show analytics for
- `shortUrl?: string` - Optional short URL for display

### UI Components

#### Button
Reusable button component with variants:
- `primary` (default) - Blue background
- `secondary` - Gray background
- `outline` - Transparent with border
- `ghost` - Transparent hover effect
- `destructive` - Red background

**Features:**
- Loading states with spinner
- Multiple sizes (sm, md, lg)
- Full accessibility support
- TypeScript props interface

#### Input
Form input component with:
- Label association
- Error state handling
- Accessibility attributes
- Consistent styling

#### Select
Dropdown select component with:
- Custom styling
- Error states
- Accessibility support
- Chevron icon

#### Toast
Notification system with:
- Multiple types (success, error, warning, info)
- Auto-dismiss functionality
- Smooth animations
- Accessibility compliance

#### LoadingSpinner
Loading indicator component with:
- Multiple sizes
- Consistent styling
- Accessibility labels

## Features Implemented

### ✅ Real-time Custom Code Availability
- Debounced API calls to check code availability
- Visual feedback (checkmark/error icon)
- Automatic suggestions when code is taken
- Form validation integration

### ✅ Responsive Design
- Mobile-first approach with Tailwind CSS
- Responsive grid layouts
- Touch-friendly interface elements
- Proper viewport handling

### ✅ Accessibility Compliance
- ARIA labels and descriptions
- Keyboard navigation support
- Screen reader compatibility
- Semantic HTML structure
- Focus management
- Error announcements

### ✅ Loading States & Error Handling
- Loading spinners during API calls
- Toast notifications for success/error
- Form validation with real-time feedback
- Graceful error recovery

### ✅ Analytics Visualization
- Interactive charts with Recharts
- Geographic data visualization
- Device and referrer analytics
- Export functionality
- Real-time data updates

## Testing

### Component Tests
- Unit tests for all components
- Accessibility testing
- Responsive design validation
- User interaction testing

### Test Files
- `__tests__/Button.test.tsx` - Button component tests
- `__tests__/Input.test.tsx` - Input component tests
- `__tests__/LinkCreator.test.tsx` - Link creation flow tests
- `__tests__/accessibility.test.tsx` - Accessibility compliance tests
- `__tests__/responsive.test.tsx` - Responsive design tests

### Running Tests
```bash
npm test                 # Run all tests
npm run test:watch      # Run tests in watch mode
npm run test:coverage   # Run tests with coverage report
```

## Dependencies

### Core Dependencies
- `react` & `react-dom` - React framework
- `next` - Next.js framework
- `typescript` - Type safety

### UI & Styling
- `tailwindcss` - Utility-first CSS framework
- `lucide-react` - Icon library
- `clsx` - Conditional class names

### Forms & Validation
- `react-hook-form` - Form handling
- `@hookform/resolvers` - Form validation resolvers
- `zod` - Schema validation (via shared package)

### Charts & Visualization
- `recharts` - Chart library for analytics

### Testing
- `@testing-library/react` - React testing utilities
- `@testing-library/jest-dom` - Jest DOM matchers
- `@testing-library/user-event` - User interaction testing
- `jest` - Testing framework

## File Structure

```
src/components/
├── ui/                          # Reusable UI components
│   ├── Button.tsx
│   ├── Input.tsx
│   ├── Select.tsx
│   ├── Toast.tsx
│   └── LoadingSpinner.tsx
├── LinkCreator.tsx              # Main link creation component
├── LinkDisplay.tsx              # Link display and actions
├── AnalyticsDashboard.tsx       # Analytics visualization
├── __tests__/                   # Component tests
│   ├── Button.test.tsx
│   ├── Input.test.tsx
│   ├── LinkCreator.test.tsx
│   ├── accessibility.test.tsx
│   └── responsive.test.tsx
└── README.md                    # This file
```

## Usage Examples

### Basic Link Creation
```tsx
import { LinkCreator } from '@/components/LinkCreator';

function App() {
  const handleLinkCreated = (link) => {
    console.log('New link created:', link.short_url);
  };

  return <LinkCreator onLinkCreated={handleLinkCreated} />;
}
```

### Display Created Link
```tsx
import { LinkDisplay } from '@/components/LinkDisplay';

function App() {
  const link = {
    short_url: 'https://go2.tools/abc123',
    code: 'abc123',
    qr_url: 'https://api.example.com/qr/abc123',
    long_url: 'https://example.com',
    base_domain: 'go2.tools',
  };

  return <LinkDisplay link={link} showAnalytics={true} />;
}
```

### Analytics Dashboard
```tsx
import { AnalyticsDashboard } from '@/components/AnalyticsDashboard';

function App() {
  return <AnalyticsDashboard code="abc123" shortUrl="https://go2.tools/abc123" />;
}
```

## Performance Considerations

- **Debounced API calls** for custom code checking
- **Lazy loading** of chart components
- **Memoized components** where appropriate
- **Optimized bundle size** with tree shaking
- **Responsive images** and assets

## Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- Mobile browsers (iOS Safari, Chrome Mobile)
- Accessibility tools and screen readers
- Progressive enhancement for older browsers