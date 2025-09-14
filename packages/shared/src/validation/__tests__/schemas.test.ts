/**
 * Unit tests for Zod validation schemas.
 * Tests validation of all data models and form inputs.
 */

import { describe, it, expect } from 'vitest';
import {
  BaseDomainSchema,
  PlanTypeSchema,
  DeviceTypeSchema,
  LinkMetadataSchema,
  LocationDataSchema,
  LinkDocumentSchema,
  ClickDocumentSchema,
  UserDocumentSchema,
  CreateLinkRequestSchema,
  CreateLinkResponseSchema,
  SafetySettingsSchema,
  PlanLimitsSchema,
  ConfigDocumentSchema,
  ErrorResponseSchema,
  SuccessResponseSchema,
} from '../schemas';

describe('Base Type Schemas', () => {
  describe('BaseDomainSchema', () => {
    it('should validate valid base domains', () => {
      expect(BaseDomainSchema.parse('go2.video')).toBe('go2.video');
      expect(BaseDomainSchema.parse('go2.reviews')).toBe('go2.reviews');
      expect(BaseDomainSchema.parse('go2.tools')).toBe('go2.tools');
    });

    it('should reject invalid base domains', () => {
      expect(() => BaseDomainSchema.parse('invalid.domain')).toThrow();
      expect(() => BaseDomainSchema.parse('go2.invalid')).toThrow();
    });
  });

  describe('PlanTypeSchema', () => {
    it('should validate valid plan types', () => {
      expect(PlanTypeSchema.parse('free')).toBe('free');
      expect(PlanTypeSchema.parse('paid')).toBe('paid');
    });

    it('should reject invalid plan types', () => {
      expect(() => PlanTypeSchema.parse('premium')).toThrow();
      expect(() => PlanTypeSchema.parse('enterprise')).toThrow();
    });
  });

  describe('DeviceTypeSchema', () => {
    it('should validate valid device types', () => {
      expect(DeviceTypeSchema.parse('mobile')).toBe('mobile');
      expect(DeviceTypeSchema.parse('desktop')).toBe('desktop');
      expect(DeviceTypeSchema.parse('tablet')).toBe('tablet');
      expect(DeviceTypeSchema.parse('unknown')).toBe('unknown');
    });

    it('should reject invalid device types', () => {
      expect(() => DeviceTypeSchema.parse('smartwatch')).toThrow();
    });
  });
});

describe('Complex Type Schemas', () => {
  describe('LinkMetadataSchema', () => {
    it('should validate valid metadata', () => {
      const validMetadata = {
        title: 'Test Title',
        host: 'example.com',
        favicon_url: 'https://example.com/favicon.ico',
      };
      expect(LinkMetadataSchema.parse(validMetadata)).toEqual(validMetadata);
    });

    it('should validate metadata with optional fields', () => {
      const minimalMetadata = {};
      expect(LinkMetadataSchema.parse(minimalMetadata)).toEqual({});
      
      const partialMetadata = { title: 'Test' };
      expect(LinkMetadataSchema.parse(partialMetadata)).toEqual(partialMetadata);
    });

    it('should reject invalid favicon URL', () => {
      const invalidMetadata = {
        favicon_url: 'not-a-url',
      };
      expect(() => LinkMetadataSchema.parse(invalidMetadata)).toThrow();
    });
  });

  describe('LocationDataSchema', () => {
    it('should validate valid location data', () => {
      const validLocation = {
        country: 'United States',
        country_code: 'US',
        region: 'California',
        city: 'San Francisco',
        timezone: 'America/Los_Angeles',
        latitude: 37.7749,
        longitude: -122.4194,
      };
      expect(LocationDataSchema.parse(validLocation)).toEqual(validLocation);
    });

    it('should validate location with null values', () => {
      const nullLocation = {
        country: null,
        country_code: null,
        region: null,
        city: null,
        timezone: null,
        latitude: null,
        longitude: null,
      };
      expect(LocationDataSchema.parse(nullLocation)).toEqual(nullLocation);
    });

    it('should reject invalid coordinates', () => {
      expect(() => LocationDataSchema.parse({ latitude: 91 })).toThrow();
      expect(() => LocationDataSchema.parse({ latitude: -91 })).toThrow();
      expect(() => LocationDataSchema.parse({ longitude: 181 })).toThrow();
      expect(() => LocationDataSchema.parse({ longitude: -181 })).toThrow();
    });

    it('should reject invalid country code length', () => {
      expect(() => LocationDataSchema.parse({ country_code: 'USA' })).toThrow();
      expect(() => LocationDataSchema.parse({ country_code: 'U' })).toThrow();
    });
  });
});

describe('Document Schemas', () => {
  describe('LinkDocumentSchema', () => {
    it('should validate valid link document', () => {
      const validLink = {
        long_url: 'https://example.com/very/long/url',
        base_domain: 'go2.video' as const,
        owner_uid: 'user123',
        password_hash: 'hashed_password',
        expires_at: new Date(Date.now() + 86400000), // Tomorrow
        disabled: false,
        created_at: new Date(),
        created_by_ip: '192.168.1.1',
        metadata: { title: 'Test' },
        plan_type: 'free' as const,
        is_custom_code: true,
      };
      expect(LinkDocumentSchema.parse(validLink)).toEqual(validLink);
    });

    it('should validate link with null optional fields', () => {
      const minimalLink = {
        long_url: 'https://example.com',
        base_domain: 'go2.tools' as const,
        owner_uid: null,
        password_hash: null,
        expires_at: null,
        disabled: false,
        created_at: new Date(),
        created_by_ip: null,
        metadata: {},
        plan_type: 'paid' as const,
        is_custom_code: false,
      };
      expect(LinkDocumentSchema.parse(minimalLink)).toEqual(minimalLink);
    });

    it('should reject invalid URL', () => {
      const invalidLink = {
        long_url: 'not-a-url',
        base_domain: 'go2.video',
        disabled: false,
        created_at: new Date(),
        metadata: {},
        plan_type: 'free',
        is_custom_code: false,
      };
      expect(() => LinkDocumentSchema.parse(invalidLink)).toThrow();
    });
  });

  describe('UserDocumentSchema', () => {
    it('should validate valid user document', () => {
      const validUser = {
        email: 'test@example.com',
        display_name: 'Test User',
        plan_type: 'paid' as const,
        custom_codes_used: 5,
        custom_codes_reset_date: new Date(),
        created_at: new Date(),
        last_login: new Date(),
        is_admin: true,
      };
      expect(UserDocumentSchema.parse(validUser)).toEqual(validUser);
    });

    it('should reject invalid email', () => {
      const invalidUser = {
        email: 'invalid-email',
        display_name: 'Test User',
        plan_type: 'free',
        custom_codes_used: 0,
        custom_codes_reset_date: new Date(),
        created_at: new Date(),
        last_login: new Date(),
        is_admin: false,
      };
      expect(() => UserDocumentSchema.parse(invalidUser)).toThrow();
    });

    it('should reject empty display name', () => {
      const invalidUser = {
        email: 'test@example.com',
        display_name: '',
        plan_type: 'free',
        custom_codes_used: 0,
        custom_codes_reset_date: new Date(),
        created_at: new Date(),
        last_login: new Date(),
        is_admin: false,
      };
      expect(() => UserDocumentSchema.parse(invalidUser)).toThrow();
    });

    it('should reject negative custom codes used', () => {
      const invalidUser = {
        email: 'test@example.com',
        display_name: 'Test User',
        plan_type: 'free',
        custom_codes_used: -1,
        custom_codes_reset_date: new Date(),
        created_at: new Date(),
        last_login: new Date(),
        is_admin: false,
      };
      expect(() => UserDocumentSchema.parse(invalidUser)).toThrow();
    });
  });

  describe('ClickDocumentSchema', () => {
    it('should validate valid click document', () => {
      const validClick = {
        ts: new Date(),
        ip_hash: 'hashed_ip',
        ua: 'Mozilla/5.0...',
        referrer: 'https://google.com',
        location: {
          country: 'United States',
          country_code: 'US',
          region: 'California',
          city: 'San Francisco',
          timezone: 'America/Los_Angeles',
          latitude: 37.7749,
          longitude: -122.4194,
        },
        device_type: 'desktop' as const,
        browser: 'Chrome',
        os: 'Windows',
      };
      expect(ClickDocumentSchema.parse(validClick)).toEqual(validClick);
    });

    it('should validate click with null optional fields', () => {
      const minimalClick = {
        ts: new Date(),
        ip_hash: null,
        ua: null,
        referrer: null,
        location: {
          country: null,
          country_code: null,
          region: null,
          city: null,
          timezone: null,
          latitude: null,
          longitude: null,
        },
        device_type: 'unknown' as const,
        browser: null,
        os: null,
      };
      expect(ClickDocumentSchema.parse(minimalClick)).toEqual(minimalClick);
    });
  });
});

describe('Request/Response Schemas', () => {
  describe('CreateLinkRequestSchema', () => {
    it('should validate valid create link request', () => {
      const validRequest = {
        long_url: 'https://example.com',
        base_domain: 'go2.video' as const,
        custom_code: 'my-code',
        password: 'secret123',
        expires_at: new Date(Date.now() + 86400000), // Tomorrow
      };
      expect(CreateLinkRequestSchema.parse(validRequest)).toEqual(validRequest);
    });

    it('should validate request with optional fields omitted', () => {
      const minimalRequest = {
        long_url: 'https://example.com',
        base_domain: 'go2.reviews' as const,
      };
      expect(CreateLinkRequestSchema.parse(minimalRequest)).toEqual(minimalRequest);
    });

    it('should reject invalid URL', () => {
      const invalidRequest = {
        long_url: 'not-a-url',
        base_domain: 'go2.video',
      };
      expect(() => CreateLinkRequestSchema.parse(invalidRequest)).toThrow();
    });

    it('should reject short custom code', () => {
      const invalidRequest = {
        long_url: 'https://example.com',
        base_domain: 'go2.video',
        custom_code: 'ab', // Too short
      };
      expect(() => CreateLinkRequestSchema.parse(invalidRequest)).toThrow();
    });

    it('should reject custom code with invalid characters', () => {
      const invalidRequest = {
        long_url: 'https://example.com',
        base_domain: 'go2.video',
        custom_code: 'invalid@code',
      };
      expect(() => CreateLinkRequestSchema.parse(invalidRequest)).toThrow();
    });

    it('should reject short password', () => {
      const invalidRequest = {
        long_url: 'https://example.com',
        base_domain: 'go2.video',
        password: '123', // Too short
      };
      expect(() => CreateLinkRequestSchema.parse(invalidRequest)).toThrow();
    });

    it('should reject past expiration date', () => {
      const invalidRequest = {
        long_url: 'https://example.com',
        base_domain: 'go2.video',
        expires_at: new Date(Date.now() - 86400000), // Yesterday
      };
      expect(() => CreateLinkRequestSchema.parse(invalidRequest)).toThrow();
    });
  });

  describe('CreateLinkResponseSchema', () => {
    it('should validate valid create link response', () => {
      const validResponse = {
        short_url: 'https://go2.video/abc123',
        code: 'abc123',
        qr_url: 'https://api.example.com/qr/abc123',
        long_url: 'https://example.com',
        base_domain: 'go2.video' as const,
        expires_at: new Date(Date.now() + 86400000),
      };
      expect(CreateLinkResponseSchema.parse(validResponse)).toEqual(validResponse);
    });

    it('should validate response without expiration', () => {
      const validResponse = {
        short_url: 'https://go2.reviews/xyz789',
        code: 'xyz789',
        qr_url: 'https://api.example.com/qr/xyz789',
        long_url: 'https://example.com',
        base_domain: 'go2.reviews' as const,
      };
      expect(CreateLinkResponseSchema.parse(validResponse)).toEqual(validResponse);
    });
  });
});

describe('Config Schemas', () => {
  describe('SafetySettingsSchema', () => {
    it('should validate valid safety settings', () => {
      const validSettings = {
        enable_safe_browsing: true,
        blacklist_domains: ['spam.com', 'malware.net'],
        blacklist_keywords: ['spam', 'phishing'],
      };
      expect(SafetySettingsSchema.parse(validSettings)).toEqual(validSettings);
    });

    it('should validate empty arrays', () => {
      const validSettings = {
        enable_safe_browsing: false,
        blacklist_domains: [],
        blacklist_keywords: [],
      };
      expect(SafetySettingsSchema.parse(validSettings)).toEqual(validSettings);
    });
  });

  describe('PlanLimitsSchema', () => {
    it('should validate valid plan limits', () => {
      const validLimits = {
        free: { custom_codes: 5 },
        paid: { custom_codes: 100 },
      };
      expect(PlanLimitsSchema.parse(validLimits)).toEqual(validLimits);
    });

    it('should reject negative limits', () => {
      const invalidLimits = {
        free: { custom_codes: -1 },
        paid: { custom_codes: 100 },
      };
      expect(() => PlanLimitsSchema.parse(invalidLimits)).toThrow();
    });
  });

  describe('ConfigDocumentSchema', () => {
    it('should validate valid config document', () => {
      const validConfig = {
        base_domains: ['go2.video', 'go2.reviews', 'go2.tools'] as const,
        domain_suggestions: {
          'youtube.com': 'go2.video' as const,
          'yelp.com': 'go2.reviews' as const,
        },
        safety_settings: {
          enable_safe_browsing: true,
          blacklist_domains: ['spam.com'],
          blacklist_keywords: ['spam'],
        },
        plan_limits: {
          free: { custom_codes: 5 },
          paid: { custom_codes: 100 },
        },
      };
      expect(ConfigDocumentSchema.parse(validConfig)).toEqual(validConfig);
    });
  });
});

describe('API Response Schemas', () => {
  describe('ErrorResponseSchema', () => {
    it('should validate valid error response', () => {
      const validError = {
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Invalid input data',
          details: { field: 'long_url', issue: 'Invalid URL' },
        },
      };
      expect(ErrorResponseSchema.parse(validError)).toEqual(validError);
    });

    it('should validate error without details', () => {
      const validError = {
        error: {
          code: 'NOT_FOUND',
          message: 'Link not found',
        },
      };
      expect(ErrorResponseSchema.parse(validError)).toEqual(validError);
    });
  });

  describe('SuccessResponseSchema', () => {
    it('should validate valid success response', () => {
      const validSuccess = {
        data: { result: 'success', id: 123 },
        message: 'Operation completed successfully',
      };
      expect(SuccessResponseSchema.parse(validSuccess)).toEqual(validSuccess);
    });

    it('should validate success without message', () => {
      const validSuccess = {
        data: { items: [1, 2, 3] },
      };
      expect(SuccessResponseSchema.parse(validSuccess)).toEqual(validSuccess);
    });
  });
});