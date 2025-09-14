import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Accessibility Tests', () => {
  test('should not have any automatically detectable accessibility issues on homepage', async ({ page }) => {
    await page.route('**/api/config/base-domains', async (route) => {
      await route.fulfill({
        json: ['go2.video', 'go2.reviews', 'go2.tools'],
      });
    });

    await page.goto('/');

    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('should not have accessibility issues on link creation form', async ({ page }) => {
    await page.route('**/api/config/base-domains', async (route) => {
      await route.fulfill({
        json: ['go2.video', 'go2.reviews', 'go2.tools'],
      });
    });

    await page.goto('/');

    // Expand all form sections to test them
    await page.click('[data-testid="custom-code-toggle"]');
    await page.click('[data-testid="password-toggle"]');
    await page.click('[data-testid="expiry-toggle"]');

    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('should not have accessibility issues on analytics dashboard', async ({ page }) => {
    await page.route('**/api/stats/test123', async (route) => {
      await route.fulfill({
        json: {
          totalClicks: 42,
          clicksByDay: [
            { date: '2024-01-01', clicks: 5 },
            { date: '2024-01-02', clicks: 8 },
          ],
          topReferrers: [
            { referrer: 'google.com', clicks: 15 },
          ],
          topDevices: [
            { device: 'desktop', clicks: 25 },
          ],
          geographicData: [
            { country: 'United States', clicks: 20 },
          ],
        },
      });
    });

    await page.goto('/analytics/test123');

    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('should have proper keyboard navigation', async ({ page }) => {
    await page.route('**/api/config/base-domains', async (route) => {
      await route.fulfill({
        json: ['go2.video', 'go2.reviews', 'go2.tools'],
      });
    });

    await page.goto('/');

    // Test tab navigation through form
    await page.keyboard.press('Tab'); // URL input
    await expect(page.locator('[data-testid="url-input"]')).toBeFocused();

    await page.keyboard.press('Tab'); // Domain select
    await expect(page.locator('[data-testid="domain-select"]')).toBeFocused();

    await page.keyboard.press('Tab'); // Custom code toggle
    await expect(page.locator('[data-testid="custom-code-toggle"]')).toBeFocused();

    await page.keyboard.press('Tab'); // Password toggle
    await expect(page.locator('[data-testid="password-toggle"]')).toBeFocused();

    await page.keyboard.press('Tab'); // Expiry toggle
    await expect(page.locator('[data-testid="expiry-toggle"]')).toBeFocused();

    await page.keyboard.press('Tab'); // Create button
    await expect(page.locator('[data-testid="create-link-button"]')).toBeFocused();
  });

  test('should have proper ARIA labels and roles', async ({ page }) => {
    await page.route('**/api/config/base-domains', async (route) => {
      await route.fulfill({
        json: ['go2.video', 'go2.reviews', 'go2.tools'],
      });
    });

    await page.goto('/');

    // Check form has proper labels
    const urlInput = page.locator('[data-testid="url-input"]');
    await expect(urlInput).toHaveAttribute('aria-label');

    const domainSelect = page.locator('[data-testid="domain-select"]');
    await expect(domainSelect).toHaveAttribute('aria-label');

    // Check buttons have proper roles and labels
    const createButton = page.locator('[data-testid="create-link-button"]');
    await expect(createButton).toHaveAttribute('role', 'button');
    await expect(createButton).toHaveAttribute('aria-label');
  });

  test('should support screen reader announcements', async ({ page }) => {
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

    await page.fill('[data-testid="url-input"]', 'https://example.com');
    await page.click('[data-testid="create-link-button"]');

    // Check for success announcement
    const successMessage = page.locator('[data-testid="success-announcement"]');
    await expect(successMessage).toHaveAttribute('aria-live', 'polite');
    await expect(successMessage).toBeVisible();
  });

  test('should have sufficient color contrast', async ({ page }) => {
    await page.route('**/api/config/base-domains', async (route) => {
      await route.fulfill({
        json: ['go2.video', 'go2.reviews', 'go2.tools'],
      });
    });

    await page.goto('/');

    // Run axe with color contrast rules specifically
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();

    const colorContrastViolations = accessibilityScanResults.violations.filter(
      violation => violation.id === 'color-contrast'
    );

    expect(colorContrastViolations).toEqual([]);
  });

  test('should work with high contrast mode', async ({ page }) => {
    // Simulate high contrast mode
    await page.emulateMedia({ colorScheme: 'dark', reducedMotion: 'reduce' });

    await page.route('**/api/config/base-domains', async (route) => {
      await route.fulfill({
        json: ['go2.video', 'go2.reviews', 'go2.tools'],
      });
    });

    await page.goto('/');

    // Verify elements are still visible and functional
    await expect(page.locator('[data-testid="url-input"]')).toBeVisible();
    await expect(page.locator('[data-testid="create-link-button"]')).toBeVisible();

    // Test form still works
    await page.fill('[data-testid="url-input"]', 'https://example.com');
    await page.click('[data-testid="create-link-button"]');
  });
});