import { test as base, expect } from '@playwright/test';
import { testUsers } from './test-data';

type AuthFixtures = {
  authenticatedPage: any;
  adminPage: any;
};

export const test = base.extend<AuthFixtures>({
  authenticatedPage: async ({ page }, use) => {
    // Mock Firebase Auth for regular user
    await page.addInitScript(() => {
      // Mock Firebase Auth
      window.mockFirebaseAuth = {
        currentUser: {
          uid: 'test-user-uid',
          email: 'user@test.com',
          displayName: 'Test User',
          getIdToken: () => Promise.resolve('mock-token'),
        },
        onAuthStateChanged: (callback: any) => {
          callback(window.mockFirebaseAuth.currentUser);
          return () => {};
        },
      };
    });

    await page.goto('/');
    await use(page);
  },

  adminPage: async ({ page }, use) => {
    // Mock Firebase Auth for admin user
    await page.addInitScript(() => {
      window.mockFirebaseAuth = {
        currentUser: {
          uid: 'test-admin-uid',
          email: 'admin@test.com',
          displayName: 'Test Admin',
          getIdToken: () => Promise.resolve('mock-admin-token'),
        },
        onAuthStateChanged: (callback: any) => {
          callback(window.mockFirebaseAuth.currentUser);
          return () => {};
        },
      };
    });

    await page.goto('/');
    await use(page);
  },
});

export { expect } from '@playwright/test';