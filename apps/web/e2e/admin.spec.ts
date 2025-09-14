import { test, expect } from './fixtures/auth-setup';
import { testLinks } from './fixtures/test-data';

test.describe('Admin Dashboard', () => {
  test('should display admin dashboard for admin users', async ({ adminPage }) => {
    // Mock admin API endpoints
    await adminPage.route('**/api/admin/links', async (route) => {
      await route.fulfill({
        json: [
          {
            code: 'test123',
            long_url: 'https://example.com',
            base_domain: 'go2.tools',
            owner_uid: 'user123',
            created_at: '2024-01-01T00:00:00Z',
            disabled: false,
            clicks: 42,
          },
          {
            code: 'test456',
            long_url: 'https://another.com',
            base_domain: 'go2.video',
            owner_uid: 'user456',
            created_at: '2024-01-02T00:00:00Z',
            disabled: true,
            clicks: 15,
          },
        ],
      });
    });

    await adminPage.route('**/api/admin/users', async (route) => {
      await route.fulfill({
        json: [
          {
            uid: 'user123',
            email: 'user1@example.com',
            display_name: 'User One',
            plan_type: 'free',
            created_at: '2024-01-01T00:00:00Z',
            links_count: 5,
          },
          {
            uid: 'user456',
            email: 'user2@example.com',
            display_name: 'User Two',
            plan_type: 'paid',
            created_at: '2024-01-02T00:00:00Z',
            links_count: 25,
          },
        ],
      });
    });

    await adminPage.goto('/admin');

    // Check admin dashboard loads
    await expect(adminPage.locator('[data-testid="admin-dashboard"]')).toBeVisible();

    // Check links management section
    await expect(adminPage.locator('[data-testid="links-table"]')).toBeVisible();
    await expect(adminPage.locator('[data-testid="link-test123"]')).toBeVisible();
    await expect(adminPage.locator('[data-testid="link-test456"]')).toBeVisible();

    // Check users management section
    await adminPage.click('[data-testid="users-tab"]');
    await expect(adminPage.locator('[data-testid="users-table"]')).toBeVisible();
    await expect(adminPage.locator('[data-testid="user-user123"]')).toBeVisible();
  });

  test('should allow admin to disable/enable links', async ({ adminPage }) => {
    await adminPage.route('**/api/admin/links', async (route) => {
      await route.fulfill({
        json: [
          {
            code: 'test123',
            long_url: 'https://example.com',
            base_domain: 'go2.tools',
            owner_uid: 'user123',
            created_at: '2024-01-01T00:00:00Z',
            disabled: false,
            clicks: 42,
          },
        ],
      });
    });

    let linkDisabled = false;
    await adminPage.route('**/api/admin/links/test123', async (route) => {
      if (route.request().method() === 'PUT') {
        linkDisabled = true;
        await route.fulfill({
          json: { success: true },
        });
      }
    });

    await adminPage.goto('/admin');

    // Disable link
    await adminPage.click('[data-testid="disable-link-test123"]');
    
    // Confirm action
    await adminPage.click('[data-testid="confirm-disable"]');

    // Verify API was called
    expect(linkDisabled).toBe(true);

    // Check success message
    await expect(adminPage.locator('[data-testid="success-message"]')).toBeVisible();
  });

  test('should allow bulk operations on links', async ({ adminPage }) => {
    await adminPage.route('**/api/admin/links', async (route) => {
      await route.fulfill({
        json: [
          {
            code: 'test123',
            long_url: 'https://example.com',
            base_domain: 'go2.tools',
            owner_uid: 'user123',
            created_at: '2024-01-01T00:00:00Z',
            disabled: false,
            clicks: 42,
          },
          {
            code: 'test456',
            long_url: 'https://another.com',
            base_domain: 'go2.video',
            owner_uid: 'user456',
            created_at: '2024-01-02T00:00:00Z',
            disabled: false,
            clicks: 15,
          },
        ],
      });
    });

    let bulkOperationCalled = false;
    await adminPage.route('**/api/admin/links/bulk', async (route) => {
      bulkOperationCalled = true;
      await route.fulfill({
        json: { success: true, affected: 2 },
      });
    });

    await adminPage.goto('/admin');

    // Select multiple links
    await adminPage.check('[data-testid="select-link-test123"]');
    await adminPage.check('[data-testid="select-link-test456"]');

    // Perform bulk disable
    await adminPage.click('[data-testid="bulk-actions-dropdown"]');
    await adminPage.click('[data-testid="bulk-disable"]');
    await adminPage.click('[data-testid="confirm-bulk-action"]');

    expect(bulkOperationCalled).toBe(true);
  });

  test('should show system statistics', async ({ adminPage }) => {
    await adminPage.route('**/api/admin/stats', async (route) => {
      await route.fulfill({
        json: {
          totalLinks: 1250,
          totalUsers: 89,
          totalClicks: 15420,
          linksToday: 23,
          clicksToday: 156,
          topDomains: [
            { domain: 'go2.video', count: 450 },
            { domain: 'go2.tools', count: 380 },
            { domain: 'go2.reviews', count: 420 },
          ],
        },
      });
    });

    await adminPage.goto('/admin');

    await adminPage.click('[data-testid="stats-tab"]');

    // Check system stats
    await expect(adminPage.locator('[data-testid="total-links"]')).toContainText('1,250');
    await expect(adminPage.locator('[data-testid="total-users"]')).toContainText('89');
    await expect(adminPage.locator('[data-testid="total-clicks"]')).toContainText('15,420');
    await expect(adminPage.locator('[data-testid="links-today"]')).toContainText('23');
  });

  test('should deny access to non-admin users', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/admin');

    // Should redirect or show access denied
    await expect(authenticatedPage.locator('[data-testid="access-denied"]')).toBeVisible();
    await expect(authenticatedPage.locator('[data-testid="access-denied"]')).toContainText('Access denied');
  });
});