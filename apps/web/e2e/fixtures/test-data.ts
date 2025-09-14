export const testUrls = {
  valid: {
    youtube: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    github: 'https://github.com/microsoft/playwright',
    google: 'https://www.google.com',
    amazon: 'https://www.amazon.com/product/123',
  },
  invalid: {
    noProtocol: 'www.example.com',
    javascript: 'javascript:alert("xss")',
    malformed: 'not-a-url',
    empty: '',
  },
};

export const testUsers = {
  admin: {
    email: 'admin@test.com',
    displayName: 'Test Admin',
    uid: 'test-admin-uid',
  },
  regularUser: {
    email: 'user@test.com',
    displayName: 'Test User',
    uid: 'test-user-uid',
  },
};

export const testLinks = {
  basic: {
    code: 'test123',
    longUrl: testUrls.valid.youtube,
    baseDomain: 'go2.video',
  },
  withPassword: {
    code: 'secure123',
    longUrl: testUrls.valid.github,
    baseDomain: 'go2.tools',
    password: 'testpass123',
  },
  expired: {
    code: 'expired123',
    longUrl: testUrls.valid.google,
    baseDomain: 'go2.reviews',
    expiresAt: new Date('2023-01-01'),
  },
};

export const mockAnalyticsData = {
  totalClicks: 42,
  clicksByDay: [
    { date: '2024-01-01', clicks: 5 },
    { date: '2024-01-02', clicks: 8 },
    { date: '2024-01-03', clicks: 12 },
  ],
  topReferrers: [
    { referrer: 'google.com', clicks: 15 },
    { referrer: 'twitter.com', clicks: 10 },
    { referrer: 'direct', clicks: 17 },
  ],
  topDevices: [
    { device: 'desktop', clicks: 25 },
    { device: 'mobile', clicks: 15 },
    { device: 'tablet', clicks: 2 },
  ],
  geographicData: [
    { country: 'United States', clicks: 20 },
    { country: 'Canada', clicks: 12 },
    { country: 'United Kingdom', clicks: 10 },
  ],
};