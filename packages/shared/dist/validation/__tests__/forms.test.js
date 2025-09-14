"use strict";
/**
 * Unit tests for form validation schemas and utilities.
 * Tests form-specific validation logic and helper functions.
 */
Object.defineProperty(exports, "__esModule", { value: true });
const vitest_1 = require("vitest");
const forms_1 = require("../forms");
(0, vitest_1.describe)('Form Schemas', () => {
    (0, vitest_1.describe)('LinkCreationFormSchema', () => {
        (0, vitest_1.it)('should validate valid link creation form', () => {
            const validForm = {
                long_url: 'https://example.com/very/long/url',
                base_domain: 'go2.video',
                custom_code: 'my-custom-code',
                password: 'secret123',
                expires_at: new Date(Date.now() + 86400000), // Tomorrow
            };
            (0, vitest_1.expect)(forms_1.LinkCreationFormSchema.parse(validForm)).toEqual(validForm);
        });
        (0, vitest_1.it)('should validate minimal form data', () => {
            const minimalForm = {
                long_url: 'https://example.com',
                base_domain: 'go2.reviews',
            };
            (0, vitest_1.expect)(forms_1.LinkCreationFormSchema.parse(minimalForm)).toEqual(minimalForm);
        });
        (0, vitest_1.it)('should reject empty URL', () => {
            const invalidForm = {
                long_url: '',
                base_domain: 'go2.video',
            };
            (0, vitest_1.expect)(() => forms_1.LinkCreationFormSchema.parse(invalidForm)).toThrow('URL is required');
        });
        (0, vitest_1.it)('should reject invalid URL format', () => {
            const invalidForm = {
                long_url: 'not-a-url',
                base_domain: 'go2.video',
            };
            (0, vitest_1.expect)(() => forms_1.LinkCreationFormSchema.parse(invalidForm)).toThrow('Please enter a valid URL');
        });
        (0, vitest_1.it)('should reject short custom code', () => {
            const invalidForm = {
                long_url: 'https://example.com',
                base_domain: 'go2.video',
                custom_code: 'ab',
            };
            (0, vitest_1.expect)(() => forms_1.LinkCreationFormSchema.parse(invalidForm)).toThrow('at least 3 characters');
        });
        (0, vitest_1.it)('should reject long custom code', () => {
            const invalidForm = {
                long_url: 'https://example.com',
                base_domain: 'go2.video',
                custom_code: 'a'.repeat(51), // 51 characters
            };
            (0, vitest_1.expect)(() => forms_1.LinkCreationFormSchema.parse(invalidForm)).toThrow('at most 50 characters');
        });
        (0, vitest_1.it)('should reject custom code with invalid characters', () => {
            const invalidForm = {
                long_url: 'https://example.com',
                base_domain: 'go2.video',
                custom_code: 'invalid@code!',
            };
            (0, vitest_1.expect)(() => forms_1.LinkCreationFormSchema.parse(invalidForm)).toThrow('letters, numbers, hyphens, and underscores');
        });
        (0, vitest_1.it)('should reject short password', () => {
            const invalidForm = {
                long_url: 'https://example.com',
                base_domain: 'go2.video',
                password: '123',
            };
            (0, vitest_1.expect)(() => forms_1.LinkCreationFormSchema.parse(invalidForm)).toThrow('at least 4 characters');
        });
        (0, vitest_1.it)('should reject long password', () => {
            const invalidForm = {
                long_url: 'https://example.com',
                base_domain: 'go2.video',
                password: 'a'.repeat(101), // 101 characters
            };
            (0, vitest_1.expect)(() => forms_1.LinkCreationFormSchema.parse(invalidForm)).toThrow('at most 100 characters');
        });
        (0, vitest_1.it)('should reject past expiration date', () => {
            const invalidForm = {
                long_url: 'https://example.com',
                base_domain: 'go2.video',
                expires_at: new Date(Date.now() - 86400000), // Yesterday
            };
            (0, vitest_1.expect)(() => forms_1.LinkCreationFormSchema.parse(invalidForm)).toThrow('must be in the future');
        });
    });
    (0, vitest_1.describe)('UserProfileFormSchema', () => {
        (0, vitest_1.it)('should validate valid user profile form', () => {
            const validForm = {
                display_name: 'John Doe',
                email: 'john@example.com',
            };
            (0, vitest_1.expect)(forms_1.UserProfileFormSchema.parse(validForm)).toEqual(validForm);
        });
        (0, vitest_1.it)('should reject empty display name', () => {
            const invalidForm = {
                display_name: '',
                email: 'john@example.com',
            };
            (0, vitest_1.expect)(() => forms_1.UserProfileFormSchema.parse(invalidForm)).toThrow('Display name is required');
        });
        (0, vitest_1.it)('should reject long display name', () => {
            const invalidForm = {
                display_name: 'a'.repeat(101), // 101 characters
                email: 'john@example.com',
            };
            (0, vitest_1.expect)(() => forms_1.UserProfileFormSchema.parse(invalidForm)).toThrow('at most 100 characters');
        });
        (0, vitest_1.it)('should reject invalid email', () => {
            const invalidForm = {
                display_name: 'John Doe',
                email: 'invalid-email',
            };
            (0, vitest_1.expect)(() => forms_1.UserProfileFormSchema.parse(invalidForm)).toThrow('valid email address');
        });
        (0, vitest_1.it)('should trim display name', () => {
            const formWithSpaces = {
                display_name: '  John Doe  ',
                email: 'john@example.com',
            };
            const result = forms_1.UserProfileFormSchema.parse(formWithSpaces);
            (0, vitest_1.expect)(result.display_name).toBe('John Doe');
        });
    });
    (0, vitest_1.describe)('PasswordProtectionFormSchema', () => {
        (0, vitest_1.it)('should validate valid password form', () => {
            const validForm = {
                password: 'secret123',
            };
            (0, vitest_1.expect)(forms_1.PasswordProtectionFormSchema.parse(validForm)).toEqual(validForm);
        });
        (0, vitest_1.it)('should reject empty password', () => {
            const invalidForm = {
                password: '',
            };
            (0, vitest_1.expect)(() => forms_1.PasswordProtectionFormSchema.parse(invalidForm)).toThrow('Password is required');
        });
        (0, vitest_1.it)('should reject long password', () => {
            const invalidForm = {
                password: 'a'.repeat(101), // 101 characters
            };
            (0, vitest_1.expect)(() => forms_1.PasswordProtectionFormSchema.parse(invalidForm)).toThrow('Password is too long');
        });
    });
    (0, vitest_1.describe)('AdminLinkUpdateFormSchema', () => {
        (0, vitest_1.it)('should validate valid admin update form', () => {
            const validForm = {
                disabled: true,
                expires_at: new Date(Date.now() + 86400000), // Tomorrow
                password: 'newsecret',
            };
            (0, vitest_1.expect)(forms_1.AdminLinkUpdateFormSchema.parse(validForm)).toEqual(validForm);
        });
        (0, vitest_1.it)('should validate form with only some fields', () => {
            const partialForm = {
                disabled: false,
            };
            (0, vitest_1.expect)(forms_1.AdminLinkUpdateFormSchema.parse(partialForm)).toEqual(partialForm);
        });
        (0, vitest_1.it)('should validate empty form', () => {
            const emptyForm = {};
            (0, vitest_1.expect)(forms_1.AdminLinkUpdateFormSchema.parse(emptyForm)).toEqual(emptyForm);
        });
        (0, vitest_1.it)('should reject past expiration date', () => {
            const invalidForm = {
                expires_at: new Date(Date.now() - 86400000), // Yesterday
            };
            (0, vitest_1.expect)(() => forms_1.AdminLinkUpdateFormSchema.parse(invalidForm)).toThrow('must be in the future');
        });
        (0, vitest_1.it)('should reject short password', () => {
            const invalidForm = {
                password: '123',
            };
            (0, vitest_1.expect)(() => forms_1.AdminLinkUpdateFormSchema.parse(invalidForm)).toThrow('at least 4 characters');
        });
    });
    (0, vitest_1.describe)('DailyReportFormSchema', () => {
        (0, vitest_1.it)('should validate valid daily report form', () => {
            const yesterday = new Date(Date.now() - 86400000); // Yesterday
            const validForm = {
                date: yesterday,
                domain_filter: 'go2.video',
                email_recipients: ['admin@example.com', 'user@example.com'],
            };
            (0, vitest_1.expect)(forms_1.DailyReportFormSchema.parse(validForm)).toEqual(validForm);
        });
        (0, vitest_1.it)('should validate minimal form', () => {
            const yesterday = new Date(Date.now() - 86400000); // Yesterday
            const minimalForm = {
                date: yesterday,
            };
            (0, vitest_1.expect)(forms_1.DailyReportFormSchema.parse(minimalForm)).toEqual(minimalForm);
        });
        (0, vitest_1.it)('should reject future date', () => {
            const invalidForm = {
                date: new Date(Date.now() + 86400000), // Tomorrow
            };
            (0, vitest_1.expect)(() => forms_1.DailyReportFormSchema.parse(invalidForm)).toThrow('cannot be in the future');
        });
        (0, vitest_1.it)('should reject invalid email in recipients', () => {
            const invalidForm = {
                date: new Date(),
                email_recipients: ['valid@example.com', 'invalid-email'],
            };
            (0, vitest_1.expect)(() => forms_1.DailyReportFormSchema.parse(invalidForm)).toThrow('Invalid email address');
        });
    });
    (0, vitest_1.describe)('AnalyticsExportFormSchema', () => {
        (0, vitest_1.it)('should validate valid export form', () => {
            const validForm = {
                format: 'json',
                period: '30d',
            };
            (0, vitest_1.expect)(forms_1.AnalyticsExportFormSchema.parse(validForm)).toEqual(validForm);
        });
        (0, vitest_1.it)('should validate CSV format', () => {
            const validForm = {
                format: 'csv',
                period: 'all',
            };
            (0, vitest_1.expect)(forms_1.AnalyticsExportFormSchema.parse(validForm)).toEqual(validForm);
        });
        (0, vitest_1.it)('should reject invalid format', () => {
            const invalidForm = {
                format: 'xml',
                period: '7d',
            };
            (0, vitest_1.expect)(() => forms_1.AnalyticsExportFormSchema.parse(invalidForm)).toThrow('JSON or CSV');
        });
        (0, vitest_1.it)('should reject invalid period', () => {
            const invalidForm = {
                format: 'json',
                period: '90d',
            };
            (0, vitest_1.expect)(() => forms_1.AnalyticsExportFormSchema.parse(invalidForm)).toThrow('7 days, 30 days, or all time');
        });
    });
});
(0, vitest_1.describe)('Validation Utilities', () => {
    (0, vitest_1.describe)('validateForm', () => {
        (0, vitest_1.it)('should return success for valid data', () => {
            const validData = {
                long_url: 'https://example.com',
                base_domain: 'go2.video',
            };
            const result = (0, forms_1.validateForm)(forms_1.LinkCreationFormSchema, validData);
            (0, vitest_1.expect)(result.success).toBe(true);
            (0, vitest_1.expect)(result.data).toEqual(validData);
            (0, vitest_1.expect)(result.errors).toBeUndefined();
        });
        (0, vitest_1.it)('should return errors for invalid data', () => {
            const invalidData = {
                long_url: 'not-a-url',
                base_domain: 'invalid-domain',
            };
            const result = (0, forms_1.validateForm)(forms_1.LinkCreationFormSchema, invalidData);
            (0, vitest_1.expect)(result.success).toBe(false);
            (0, vitest_1.expect)(result.data).toBeUndefined();
            (0, vitest_1.expect)(result.errors).toBeDefined();
            (0, vitest_1.expect)(result.errors['long_url']).toContain('valid URL');
            (0, vitest_1.expect)(result.errors['base_domain']).toBeDefined();
        });
        (0, vitest_1.it)('should handle nested field errors', () => {
            const invalidData = {
                long_url: 'https://example.com',
                base_domain: 'go2.video',
                custom_code: 'ab', // Too short
            };
            const result = (0, forms_1.validateForm)(forms_1.LinkCreationFormSchema, invalidData);
            (0, vitest_1.expect)(result.success).toBe(false);
            (0, vitest_1.expect)(result.errors['custom_code']).toContain('at least 3 characters');
        });
    });
    (0, vitest_1.describe)('validateField', () => {
        (0, vitest_1.it)('should return success for valid field value', () => {
            const result = (0, forms_1.validateField)(forms_1.LinkCreationFormSchema.shape.long_url, 'https://example.com');
            (0, vitest_1.expect)(result.success).toBe(true);
            (0, vitest_1.expect)(result.error).toBeUndefined();
        });
        (0, vitest_1.it)('should return error for invalid field value', () => {
            const result = (0, forms_1.validateField)(forms_1.LinkCreationFormSchema.shape.long_url, 'not-a-url');
            (0, vitest_1.expect)(result.success).toBe(false);
            (0, vitest_1.expect)(result.error).toContain('valid URL');
        });
    });
    (0, vitest_1.describe)('Pre-built validators', () => {
        (0, vitest_1.describe)('urlValidator', () => {
            (0, vitest_1.it)('should validate valid URLs', () => {
                (0, vitest_1.expect)((0, forms_1.urlValidator)('https://example.com').success).toBe(true);
                (0, vitest_1.expect)((0, forms_1.urlValidator)('http://test.org').success).toBe(true);
                (0, vitest_1.expect)((0, forms_1.urlValidator)('https://sub.domain.com/path?query=1').success).toBe(true);
            });
            (0, vitest_1.it)('should reject invalid URLs', () => {
                (0, vitest_1.expect)((0, forms_1.urlValidator)('not-a-url').success).toBe(false);
                (0, vitest_1.expect)((0, forms_1.urlValidator)('ftp://example.com').success).toBe(false);
                (0, vitest_1.expect)((0, forms_1.urlValidator)('').success).toBe(false);
            });
        });
        (0, vitest_1.describe)('emailValidator', () => {
            (0, vitest_1.it)('should validate valid emails', () => {
                (0, vitest_1.expect)((0, forms_1.emailValidator)('test@example.com').success).toBe(true);
                (0, vitest_1.expect)((0, forms_1.emailValidator)('user.name+tag@domain.co.uk').success).toBe(true);
            });
            (0, vitest_1.it)('should reject invalid emails', () => {
                (0, vitest_1.expect)((0, forms_1.emailValidator)('invalid-email').success).toBe(false);
                (0, vitest_1.expect)((0, forms_1.emailValidator)('test@').success).toBe(false);
                (0, vitest_1.expect)((0, forms_1.emailValidator)('@example.com').success).toBe(false);
            });
        });
        (0, vitest_1.describe)('customCodeValidator', () => {
            (0, vitest_1.it)('should validate valid custom codes', () => {
                (0, vitest_1.expect)((0, forms_1.customCodeValidator)('abc').success).toBe(true);
                (0, vitest_1.expect)((0, forms_1.customCodeValidator)('my-code').success).toBe(true);
                (0, vitest_1.expect)((0, forms_1.customCodeValidator)('code_123').success).toBe(true);
                (0, vitest_1.expect)((0, forms_1.customCodeValidator)('a'.repeat(50)).success).toBe(true); // Max length
            });
            (0, vitest_1.it)('should reject invalid custom codes', () => {
                (0, vitest_1.expect)((0, forms_1.customCodeValidator)('ab').success).toBe(false); // Too short
                (0, vitest_1.expect)((0, forms_1.customCodeValidator)('a'.repeat(51)).success).toBe(false); // Too long
                (0, vitest_1.expect)((0, forms_1.customCodeValidator)('invalid@code').success).toBe(false); // Invalid chars
                (0, vitest_1.expect)((0, forms_1.customCodeValidator)('code with spaces').success).toBe(false); // Spaces
            });
        });
        (0, vitest_1.describe)('passwordValidator', () => {
            (0, vitest_1.it)('should validate valid passwords', () => {
                (0, vitest_1.expect)((0, forms_1.passwordValidator)('1234').success).toBe(true); // Min length
                (0, vitest_1.expect)((0, forms_1.passwordValidator)('secret123').success).toBe(true);
                (0, vitest_1.expect)((0, forms_1.passwordValidator)('a'.repeat(100)).success).toBe(true); // Max length
            });
            (0, vitest_1.it)('should reject invalid passwords', () => {
                (0, vitest_1.expect)((0, forms_1.passwordValidator)('123').success).toBe(false); // Too short
                (0, vitest_1.expect)((0, forms_1.passwordValidator)('a'.repeat(101)).success).toBe(false); // Too long
                (0, vitest_1.expect)((0, forms_1.passwordValidator)('').success).toBe(false); // Empty
            });
        });
    });
});
