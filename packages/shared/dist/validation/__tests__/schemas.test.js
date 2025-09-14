"use strict";
/**
 * Unit tests for Zod validation schemas.
 * Tests validation of all data models and form inputs.
 */
Object.defineProperty(exports, "__esModule", { value: true });
const vitest_1 = require("vitest");
const schemas_1 = require("../schemas");
(0, vitest_1.describe)('Base Type Schemas', () => {
    (0, vitest_1.describe)('BaseDomainSchema', () => {
        (0, vitest_1.it)('should validate valid base domains', () => {
            (0, vitest_1.expect)(schemas_1.BaseDomainSchema.parse('go2.video')).toBe('go2.video');
            (0, vitest_1.expect)(schemas_1.BaseDomainSchema.parse('go2.reviews')).toBe('go2.reviews');
            (0, vitest_1.expect)(schemas_1.BaseDomainSchema.parse('go2.tools')).toBe('go2.tools');
        });
        (0, vitest_1.it)('should reject invalid base domains', () => {
            (0, vitest_1.expect)(() => schemas_1.BaseDomainSchema.parse('invalid.domain')).toThrow();
            (0, vitest_1.expect)(() => schemas_1.BaseDomainSchema.parse('go2.invalid')).toThrow();
        });
    });
    (0, vitest_1.describe)('PlanTypeSchema', () => {
        (0, vitest_1.it)('should validate valid plan types', () => {
            (0, vitest_1.expect)(schemas_1.PlanTypeSchema.parse('free')).toBe('free');
            (0, vitest_1.expect)(schemas_1.PlanTypeSchema.parse('paid')).toBe('paid');
        });
        (0, vitest_1.it)('should reject invalid plan types', () => {
            (0, vitest_1.expect)(() => schemas_1.PlanTypeSchema.parse('premium')).toThrow();
            (0, vitest_1.expect)(() => schemas_1.PlanTypeSchema.parse('enterprise')).toThrow();
        });
    });
    (0, vitest_1.describe)('DeviceTypeSchema', () => {
        (0, vitest_1.it)('should validate valid device types', () => {
            (0, vitest_1.expect)(schemas_1.DeviceTypeSchema.parse('mobile')).toBe('mobile');
            (0, vitest_1.expect)(schemas_1.DeviceTypeSchema.parse('desktop')).toBe('desktop');
            (0, vitest_1.expect)(schemas_1.DeviceTypeSchema.parse('tablet')).toBe('tablet');
            (0, vitest_1.expect)(schemas_1.DeviceTypeSchema.parse('unknown')).toBe('unknown');
        });
        (0, vitest_1.it)('should reject invalid device types', () => {
            (0, vitest_1.expect)(() => schemas_1.DeviceTypeSchema.parse('smartwatch')).toThrow();
        });
    });
});
(0, vitest_1.describe)('Complex Type Schemas', () => {
    (0, vitest_1.describe)('LinkMetadataSchema', () => {
        (0, vitest_1.it)('should validate valid metadata', () => {
            const validMetadata = {
                title: 'Test Title',
                host: 'example.com',
                favicon_url: 'https://example.com/favicon.ico',
            };
            (0, vitest_1.expect)(schemas_1.LinkMetadataSchema.parse(validMetadata)).toEqual(validMetadata);
        });
        (0, vitest_1.it)('should validate metadata with optional fields', () => {
            const minimalMetadata = {};
            (0, vitest_1.expect)(schemas_1.LinkMetadataSchema.parse(minimalMetadata)).toEqual({});
            const partialMetadata = { title: 'Test' };
            (0, vitest_1.expect)(schemas_1.LinkMetadataSchema.parse(partialMetadata)).toEqual(partialMetadata);
        });
        (0, vitest_1.it)('should reject invalid favicon URL', () => {
            const invalidMetadata = {
                favicon_url: 'not-a-url',
            };
            (0, vitest_1.expect)(() => schemas_1.LinkMetadataSchema.parse(invalidMetadata)).toThrow();
        });
    });
    (0, vitest_1.describe)('LocationDataSchema', () => {
        (0, vitest_1.it)('should validate valid location data', () => {
            const validLocation = {
                country: 'United States',
                country_code: 'US',
                region: 'California',
                city: 'San Francisco',
                timezone: 'America/Los_Angeles',
                latitude: 37.7749,
                longitude: -122.4194,
            };
            (0, vitest_1.expect)(schemas_1.LocationDataSchema.parse(validLocation)).toEqual(validLocation);
        });
        (0, vitest_1.it)('should validate location with null values', () => {
            const nullLocation = {
                country: null,
                country_code: null,
                region: null,
                city: null,
                timezone: null,
                latitude: null,
                longitude: null,
            };
            (0, vitest_1.expect)(schemas_1.LocationDataSchema.parse(nullLocation)).toEqual(nullLocation);
        });
        (0, vitest_1.it)('should reject invalid coordinates', () => {
            (0, vitest_1.expect)(() => schemas_1.LocationDataSchema.parse({ latitude: 91 })).toThrow();
            (0, vitest_1.expect)(() => schemas_1.LocationDataSchema.parse({ latitude: -91 })).toThrow();
            (0, vitest_1.expect)(() => schemas_1.LocationDataSchema.parse({ longitude: 181 })).toThrow();
            (0, vitest_1.expect)(() => schemas_1.LocationDataSchema.parse({ longitude: -181 })).toThrow();
        });
        (0, vitest_1.it)('should reject invalid country code length', () => {
            (0, vitest_1.expect)(() => schemas_1.LocationDataSchema.parse({ country_code: 'USA' })).toThrow();
            (0, vitest_1.expect)(() => schemas_1.LocationDataSchema.parse({ country_code: 'U' })).toThrow();
        });
    });
});
(0, vitest_1.describe)('Document Schemas', () => {
    (0, vitest_1.describe)('LinkDocumentSchema', () => {
        (0, vitest_1.it)('should validate valid link document', () => {
            const validLink = {
                long_url: 'https://example.com/very/long/url',
                base_domain: 'go2.video',
                owner_uid: 'user123',
                password_hash: 'hashed_password',
                expires_at: new Date(Date.now() + 86400000), // Tomorrow
                disabled: false,
                created_at: new Date(),
                created_by_ip: '192.168.1.1',
                metadata: { title: 'Test' },
                plan_type: 'free',
                is_custom_code: true,
            };
            (0, vitest_1.expect)(schemas_1.LinkDocumentSchema.parse(validLink)).toEqual(validLink);
        });
        (0, vitest_1.it)('should validate link with null optional fields', () => {
            const minimalLink = {
                long_url: 'https://example.com',
                base_domain: 'go2.tools',
                owner_uid: null,
                password_hash: null,
                expires_at: null,
                disabled: false,
                created_at: new Date(),
                created_by_ip: null,
                metadata: {},
                plan_type: 'paid',
                is_custom_code: false,
            };
            (0, vitest_1.expect)(schemas_1.LinkDocumentSchema.parse(minimalLink)).toEqual(minimalLink);
        });
        (0, vitest_1.it)('should reject invalid URL', () => {
            const invalidLink = {
                long_url: 'not-a-url',
                base_domain: 'go2.video',
                disabled: false,
                created_at: new Date(),
                metadata: {},
                plan_type: 'free',
                is_custom_code: false,
            };
            (0, vitest_1.expect)(() => schemas_1.LinkDocumentSchema.parse(invalidLink)).toThrow();
        });
    });
    (0, vitest_1.describe)('UserDocumentSchema', () => {
        (0, vitest_1.it)('should validate valid user document', () => {
            const validUser = {
                email: 'test@example.com',
                display_name: 'Test User',
                plan_type: 'paid',
                custom_codes_used: 5,
                custom_codes_reset_date: new Date(),
                created_at: new Date(),
                last_login: new Date(),
                is_admin: true,
            };
            (0, vitest_1.expect)(schemas_1.UserDocumentSchema.parse(validUser)).toEqual(validUser);
        });
        (0, vitest_1.it)('should reject invalid email', () => {
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
            (0, vitest_1.expect)(() => schemas_1.UserDocumentSchema.parse(invalidUser)).toThrow();
        });
        (0, vitest_1.it)('should reject empty display name', () => {
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
            (0, vitest_1.expect)(() => schemas_1.UserDocumentSchema.parse(invalidUser)).toThrow();
        });
        (0, vitest_1.it)('should reject negative custom codes used', () => {
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
            (0, vitest_1.expect)(() => schemas_1.UserDocumentSchema.parse(invalidUser)).toThrow();
        });
    });
    (0, vitest_1.describe)('ClickDocumentSchema', () => {
        (0, vitest_1.it)('should validate valid click document', () => {
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
                device_type: 'desktop',
                browser: 'Chrome',
                os: 'Windows',
            };
            (0, vitest_1.expect)(schemas_1.ClickDocumentSchema.parse(validClick)).toEqual(validClick);
        });
        (0, vitest_1.it)('should validate click with null optional fields', () => {
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
                device_type: 'unknown',
                browser: null,
                os: null,
            };
            (0, vitest_1.expect)(schemas_1.ClickDocumentSchema.parse(minimalClick)).toEqual(minimalClick);
        });
    });
});
(0, vitest_1.describe)('Request/Response Schemas', () => {
    (0, vitest_1.describe)('CreateLinkRequestSchema', () => {
        (0, vitest_1.it)('should validate valid create link request', () => {
            const validRequest = {
                long_url: 'https://example.com',
                base_domain: 'go2.video',
                custom_code: 'my-code',
                password: 'secret123',
                expires_at: new Date(Date.now() + 86400000), // Tomorrow
            };
            (0, vitest_1.expect)(schemas_1.CreateLinkRequestSchema.parse(validRequest)).toEqual(validRequest);
        });
        (0, vitest_1.it)('should validate request with optional fields omitted', () => {
            const minimalRequest = {
                long_url: 'https://example.com',
                base_domain: 'go2.reviews',
            };
            (0, vitest_1.expect)(schemas_1.CreateLinkRequestSchema.parse(minimalRequest)).toEqual(minimalRequest);
        });
        (0, vitest_1.it)('should reject invalid URL', () => {
            const invalidRequest = {
                long_url: 'not-a-url',
                base_domain: 'go2.video',
            };
            (0, vitest_1.expect)(() => schemas_1.CreateLinkRequestSchema.parse(invalidRequest)).toThrow();
        });
        (0, vitest_1.it)('should reject short custom code', () => {
            const invalidRequest = {
                long_url: 'https://example.com',
                base_domain: 'go2.video',
                custom_code: 'ab', // Too short
            };
            (0, vitest_1.expect)(() => schemas_1.CreateLinkRequestSchema.parse(invalidRequest)).toThrow();
        });
        (0, vitest_1.it)('should reject custom code with invalid characters', () => {
            const invalidRequest = {
                long_url: 'https://example.com',
                base_domain: 'go2.video',
                custom_code: 'invalid@code',
            };
            (0, vitest_1.expect)(() => schemas_1.CreateLinkRequestSchema.parse(invalidRequest)).toThrow();
        });
        (0, vitest_1.it)('should reject short password', () => {
            const invalidRequest = {
                long_url: 'https://example.com',
                base_domain: 'go2.video',
                password: '123', // Too short
            };
            (0, vitest_1.expect)(() => schemas_1.CreateLinkRequestSchema.parse(invalidRequest)).toThrow();
        });
        (0, vitest_1.it)('should reject past expiration date', () => {
            const invalidRequest = {
                long_url: 'https://example.com',
                base_domain: 'go2.video',
                expires_at: new Date(Date.now() - 86400000), // Yesterday
            };
            (0, vitest_1.expect)(() => schemas_1.CreateLinkRequestSchema.parse(invalidRequest)).toThrow();
        });
    });
    (0, vitest_1.describe)('CreateLinkResponseSchema', () => {
        (0, vitest_1.it)('should validate valid create link response', () => {
            const validResponse = {
                short_url: 'https://go2.video/abc123',
                code: 'abc123',
                qr_url: 'https://api.example.com/qr/abc123',
                long_url: 'https://example.com',
                base_domain: 'go2.video',
                expires_at: new Date(Date.now() + 86400000),
            };
            (0, vitest_1.expect)(schemas_1.CreateLinkResponseSchema.parse(validResponse)).toEqual(validResponse);
        });
        (0, vitest_1.it)('should validate response without expiration', () => {
            const validResponse = {
                short_url: 'https://go2.reviews/xyz789',
                code: 'xyz789',
                qr_url: 'https://api.example.com/qr/xyz789',
                long_url: 'https://example.com',
                base_domain: 'go2.reviews',
            };
            (0, vitest_1.expect)(schemas_1.CreateLinkResponseSchema.parse(validResponse)).toEqual(validResponse);
        });
    });
});
(0, vitest_1.describe)('Config Schemas', () => {
    (0, vitest_1.describe)('SafetySettingsSchema', () => {
        (0, vitest_1.it)('should validate valid safety settings', () => {
            const validSettings = {
                enable_safe_browsing: true,
                blacklist_domains: ['spam.com', 'malware.net'],
                blacklist_keywords: ['spam', 'phishing'],
            };
            (0, vitest_1.expect)(schemas_1.SafetySettingsSchema.parse(validSettings)).toEqual(validSettings);
        });
        (0, vitest_1.it)('should validate empty arrays', () => {
            const validSettings = {
                enable_safe_browsing: false,
                blacklist_domains: [],
                blacklist_keywords: [],
            };
            (0, vitest_1.expect)(schemas_1.SafetySettingsSchema.parse(validSettings)).toEqual(validSettings);
        });
    });
    (0, vitest_1.describe)('PlanLimitsSchema', () => {
        (0, vitest_1.it)('should validate valid plan limits', () => {
            const validLimits = {
                free: { custom_codes: 5 },
                paid: { custom_codes: 100 },
            };
            (0, vitest_1.expect)(schemas_1.PlanLimitsSchema.parse(validLimits)).toEqual(validLimits);
        });
        (0, vitest_1.it)('should reject negative limits', () => {
            const invalidLimits = {
                free: { custom_codes: -1 },
                paid: { custom_codes: 100 },
            };
            (0, vitest_1.expect)(() => schemas_1.PlanLimitsSchema.parse(invalidLimits)).toThrow();
        });
    });
    (0, vitest_1.describe)('ConfigDocumentSchema', () => {
        (0, vitest_1.it)('should validate valid config document', () => {
            const validConfig = {
                base_domains: ['go2.video', 'go2.reviews', 'go2.tools'],
                domain_suggestions: {
                    'youtube.com': 'go2.video',
                    'yelp.com': 'go2.reviews',
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
            (0, vitest_1.expect)(schemas_1.ConfigDocumentSchema.parse(validConfig)).toEqual(validConfig);
        });
    });
});
(0, vitest_1.describe)('API Response Schemas', () => {
    (0, vitest_1.describe)('ErrorResponseSchema', () => {
        (0, vitest_1.it)('should validate valid error response', () => {
            const validError = {
                error: {
                    code: 'VALIDATION_ERROR',
                    message: 'Invalid input data',
                    details: { field: 'long_url', issue: 'Invalid URL' },
                },
            };
            (0, vitest_1.expect)(schemas_1.ErrorResponseSchema.parse(validError)).toEqual(validError);
        });
        (0, vitest_1.it)('should validate error without details', () => {
            const validError = {
                error: {
                    code: 'NOT_FOUND',
                    message: 'Link not found',
                },
            };
            (0, vitest_1.expect)(schemas_1.ErrorResponseSchema.parse(validError)).toEqual(validError);
        });
    });
    (0, vitest_1.describe)('SuccessResponseSchema', () => {
        (0, vitest_1.it)('should validate valid success response', () => {
            const validSuccess = {
                data: { result: 'success', id: 123 },
                message: 'Operation completed successfully',
            };
            (0, vitest_1.expect)(schemas_1.SuccessResponseSchema.parse(validSuccess)).toEqual(validSuccess);
        });
        (0, vitest_1.it)('should validate success without message', () => {
            const validSuccess = {
                data: { items: [1, 2, 3] },
            };
            (0, vitest_1.expect)(schemas_1.SuccessResponseSchema.parse(validSuccess)).toEqual(validSuccess);
        });
    });
});
