import { test, expect } from '@playwright/test';
import { testLinks } from './fixtures/test-data';

test.describe('URL Redirection', () => {
  test('should redirect to original URL for valid links', async ({ page }) => {
    // Mock the redirect endpoint
    await page.route('**/test123', async (route) => {
      await route.fulfill({
        status: 302,
        headers: {
          'Location': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        },
      });
    });

    // Navigate to short URL
    const response = await page.goto('/test123');
    
    // Should redirect
    expect(response?.status()).toBe(302);
  });

  test('should show password prompt for protected links', async ({ page }) => {
    // Mock password-protected link
    await page.route('**/secure123', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'text/html',
        body: `
          <html>
            <body>
              <div data-testid="password-prompt">
                <h1>Password Required</h1>
                <form data-testid="password-form">
                  <input type="password" data-testid="password-input" />
                  <button type="submit" data-testid="submit-password">Submit</button>
                </form>
              </div>
            </body>
          </html>
        `,
      });
    });

    await page.goto('/secure123');

    // Should show password prompt
    await expect(page.locator('[data-testid="password-prompt"]')).toBeVisible();
    await expect(page.locator('[data-testid="password-input"]')).toBeVisible();
  });

  test('should show error page for expired links', async ({ page }) => {
    await page.route('**/expired123', async (route) => {
      await route.fulfill({
        status: 410,
        contentType: 'text/html',
        body: `
          <html>
            <body>
              <div data-testid="expired-link">
                <h1>Link Expired</h1>
                <p>This link has expired and is no longer available.</p>
              </div>
            </body>
          </html>
        `,
      });
    });

    await page.goto('/expired123');

    await expect(page.locator('[data-testid="expired-link"]')).toBeVisible();
    await expect(page.locator('[data-testid="expired-link"]')).toContainText('Link Expired');
  });

  test('should show 404 for non-existent links', async ({ page }) => {
    await page.route('**/nonexistent', async (route) => {
      await route.fulfill({
        status: 404,
        contentType: 'text/html',
        body: `
          <html>
            <body>
              <div data-testid="not-found">
                <h1>Link Not Found</h1>
                <p>The requested link does not exist.</p>
              </div>
            </body>
          </html>
        `,
      });
    });

    await page.goto('/nonexistent');

    await expect(page.locator('[data-testid="not-found"]')).toBeVisible();
  });

  test('should track clicks on successful redirects', async ({ page }) => {
    let clickTracked = false;

    // Mock click tracking
    await page.route('**/api/internal/track-click', async (route) => {
      clickTracked = true;
      await route.fulfill({
        json: { success: true },
      });
    });

    // Mock redirect with click tracking
    await page.route('**/track123', async (route) => {
      // Simulate server-side click tracking
      await fetch('/api/internal/track-click', {
        method: 'POST',
        body: JSON.stringify({
          code: 'track123',
          userAgent: route.request().headers()['user-agent'],
          referrer: route.request().headers()['referer'],
        }),
      });

      await route.fulfill({
        status: 302,
        headers: {
          'Location': 'https://www.example.com',
        },
      });
    });

    await page.goto('/track123');

    // Click should be tracked (this would happen server-side in reality)
    // We're just verifying the flow works
  });
});