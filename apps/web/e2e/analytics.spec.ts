import { test, expect } from './fixtures/auth-setup';
import { mockAnalyticsData } from './fixtures/test-data';

test.describe('Analytics Dashboard', () => {
  test('should display analytics for a link', async ({ authenticatedPage }) => {
    // Mock analytics API
    await authenticatedPage.route('**/api/stats/test123', async (route) => {
      await route.fulfill({
        json: mockAnalyticsData,
      });
    });

    await authenticatedPage.goto('/analytics/test123');

    // Check total clicks
    await expect(authenticatedPage.locator('[data-testid="total-clicks"]')).toContainText('42');

    // Check chart is rendered
    await expect(authenticatedPage.locator('[data-testid="clicks-chart"]')).toBeVisible();

    // Check referrers table
    await expect(authenticatedPage.locator('[data-testid="referrers-table"]')).toBeVisible();
    await expect(authenticatedPage.locator('[data-testid="referrer-google.com"]')).toContainText('15');

    // Check devices breakdown
    await expect(authenticatedPage.locator('[data-testid="devices-chart"]')).toBeVisible();

    // Check geographic data
    await expect(authenticatedPage.locator('[data-testid="geographic-chart"]')).toBeVisible();
  });

  test('should handle export functionality', async ({ authenticatedPage }) => {
    await authenticatedPage.route('**/api/stats/test123', async (route) => {
      await route.fulfill({
        json: mockAnalyticsData,
      });
    });

    await authenticatedPage.route('**/api/stats/test123/export?format=csv', async (route) => {
      await route.fulfill({
        headers: {
          'Content-Type': 'text/csv',
          'Content-Disposition': 'attachment; filename="analytics-test123.csv"',
        },
        body: 'date,clicks\n2024-01-01,5\n2024-01-02,8\n2024-01-03,12',
      });
    });

    await authenticatedPage.goto('/analytics/test123');

    // Start download
    const downloadPromise = authenticatedPage.waitForEvent('download');
    await authenticatedPage.click('[data-testid="export-csv-button"]');
    const download = await downloadPromise;

    // Verify download
    expect(download.suggestedFilename()).toBe('analytics-test123.csv');
  });

  test('should show empty state for links with no clicks', async ({ authenticatedPage }) => {
    await authenticatedPage.route('**/api/stats/noclick123', async (route) => {
      await route.fulfill({
        json: {
          totalClicks: 0,
          clicksByDay: [],
          topReferrers: [],
          topDevices: [],
          geographicData: [],
        },
      });
    });

    await authenticatedPage.goto('/analytics/noclick123');

    await expect(authenticatedPage.locator('[data-testid="total-clicks"]')).toContainText('0');
    await expect(authenticatedPage.locator('[data-testid="empty-state"]')).toBeVisible();
    await expect(authenticatedPage.locator('[data-testid="empty-state"]')).toContainText('No clicks yet');
  });

  test('should handle analytics API errors', async ({ authenticatedPage }) => {
    await authenticatedPage.route('**/api/stats/error123', async (route) => {
      await route.fulfill({
        status: 404,
        json: {
          error: {
            code: 'LINK_NOT_FOUND',
            message: 'Link not found',
          },
        },
      });
    });

    await authenticatedPage.goto('/analytics/error123');

    await expect(authenticatedPage.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(authenticatedPage.locator('[data-testid="error-message"]')).toContainText('Link not found');
  });

  test('should be responsive on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE

    await page.route('**/api/stats/test123', async (route) => {
      await route.fulfill({
        json: mockAnalyticsData,
      });
    });

    await page.goto('/analytics/test123');

    // Check mobile layout
    await expect(page.locator('[data-testid="mobile-analytics-layout"]')).toBeVisible();
    
    // Charts should stack vertically on mobile
    const chartsContainer = page.locator('[data-testid="charts-container"]');
    await expect(chartsContainer).toHaveCSS('flex-direction', 'column');
  });
});