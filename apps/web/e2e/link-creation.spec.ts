import { test, expect } from './fixtures/auth-setup';
import { testUrls } from './fixtures/test-data';

test.describe('Link Creation Flow', () => {
  test('should create a basic short link', async ({ page }) => {
    // Mock API responses
    await page.route('**/api/config/base-domains', async (route) => {
      await route.fulfill({
        json: ['go2.video', 'go2.reviews', 'go2.tools'],
      });
    });

    await page.route('**/api/links/shorten', async (route) => {
      await route.fulfill({
        json: {
          code: 'abc123',
          short_url: 'https://go2.video/abc123',
          qr_url: 'https://go2.video/api/qr/abc123',
        },
      });
    });

    await page.goto('/');

    // Fill in the URL
    await page.fill('[data-testid="url-input"]', testUrls.valid.youtube);

    // Select domain (should auto-select go2.video for YouTube)
    const domainSelect = page.locator('[data-testid="domain-select"]');
    await expect(domainSelect).toHaveValue('go2.video');

    // Submit form
    await page.click('[data-testid="create-link-button"]');

    // Verify success
    await expect(page.locator('[data-testid="short-url"]')).toBeVisible();
    await expect(page.locator('[data-testid="short-url"]')).toContainText('go2.video/abc123');
  });

  test('should create a link with custom code', async ({ authenticatedPage }) => {
    await authenticatedPage.route('**/api/config/base-domains', async (route) => {
      await route.fulfill({
        json: ['go2.video', 'go2.reviews', 'go2.tools'],
      });
    });

    await authenticatedPage.route('**/api/links/shorten', async (route) => {
      await route.fulfill({
        json: {
          code: 'mycustomcode',
          short_url: 'https://go2.tools/mycustomcode',
          qr_url: 'https://go2.tools/api/qr/mycustomcode',
        },
      });
    });

    await authenticatedPage.goto('/');

    // Fill in the URL
    await authenticatedPage.fill('[data-testid="url-input"]', testUrls.valid.github);

    // Select domain
    await authenticatedPage.selectOption('[data-testid="domain-select"]', 'go2.tools');

    // Expand custom code section
    await authenticatedPage.click('[data-testid="custom-code-toggle"]');

    // Enter custom code
    await authenticatedPage.fill('[data-testid="custom-code-input"]', 'mycustomcode');

    // Submit form
    await authenticatedPage.click('[data-testid="create-link-button"]');

    // Verify success
    await expect(authenticatedPage.locator('[data-testid="short-url"]')).toContainText('go2.tools/mycustomcode');
  });

  test('should create a password-protected link', async ({ authenticatedPage }) => {
    await authenticatedPage.route('**/api/config/base-domains', async (route) => {
      await route.fulfill({
        json: ['go2.video', 'go2.reviews', 'go2.tools'],
      });
    });

    await authenticatedPage.route('**/api/links/shorten', async (route) => {
      await route.fulfill({
        json: {
          code: 'protected123',
          short_url: 'https://go2.reviews/protected123',
          qr_url: 'https://go2.reviews/api/qr/protected123',
        },
      });
    });

    await authenticatedPage.goto('/');

    // Fill in the URL
    await authenticatedPage.fill('[data-testid="url-input"]', testUrls.valid.amazon);

    // Select domain
    await authenticatedPage.selectOption('[data-testid="domain-select"]', 'go2.reviews');

    // Expand password section
    await authenticatedPage.click('[data-testid="password-toggle"]');

    // Enter password
    await authenticatedPage.fill('[data-testid="password-input"]', 'secretpass');

    // Submit form
    await authenticatedPage.click('[data-testid="create-link-button"]');

    // Verify success
    await expect(authenticatedPage.locator('[data-testid="short-url"]')).toContainText('go2.reviews/protected123');
    await expect(authenticatedPage.locator('[data-testid="password-protected-indicator"]')).toBeVisible();
  });

  test('should handle validation errors', async ({ page }) => {
    await page.goto('/');

    // Try to submit empty form
    await page.click('[data-testid="create-link-button"]');

    // Should show validation error
    await expect(page.locator('[data-testid="url-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="url-error"]')).toContainText('URL is required');

    // Try invalid URL
    await page.fill('[data-testid="url-input"]', 'not-a-url');
    await page.click('[data-testid="create-link-button"]');

    await expect(page.locator('[data-testid="url-error"]')).toContainText('Please enter a valid URL');
  });

  test('should handle API errors gracefully', async ({ page }) => {
    await page.route('**/api/config/base-domains', async (route) => {
      await route.fulfill({
        json: ['go2.video', 'go2.reviews', 'go2.tools'],
      });
    });

    await page.route('**/api/links/shorten', async (route) => {
      await route.fulfill({
        status: 403,
        json: {
          error: {
            code: 'SAFETY_VIOLATION',
            message: 'URL blocked by safety filters',
          },
        },
      });
    });

    await page.goto('/');

    await page.fill('[data-testid="url-input"]', testUrls.valid.youtube);
    await page.click('[data-testid="create-link-button"]');

    // Should show error message
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-message"]')).toContainText('URL blocked by safety filters');
  });
});