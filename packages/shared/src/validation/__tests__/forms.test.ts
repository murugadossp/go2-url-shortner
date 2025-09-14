/**
 * Unit tests for form validation schemas and utilities.
 * Tests form-specific validation logic and helper functions.
 */

import { describe, it, expect } from 'vitest';
import {
  LinkCreationFormSchema,
  UserProfileFormSchema,
  PasswordProtectionFormSchema,
  AdminLinkUpdateFormSchema,
  DailyReportFormSchema,
  AnalyticsExportFormSchema,
  validateForm,
  validateField,
  urlValidator,
  emailValidator,
  customCodeValidator,
  passwordValidator,
} from '../forms';

describe('Form Schemas', () => {
  describe('LinkCreationFormSchema', () => {
    it('should validate valid link creation form', () => {
      const validForm = {
        long_url: 'https://example.com/very/long/url',
        base_domain: 'go2.video' as const,
        custom_code: 'my-custom-code',
        password: 'secret123',
        expires_at: new Date(Date.now() + 86400000), // Tomorrow
      };
      expect(LinkCreationFormSchema.parse(validForm)).toEqual(validForm);
    });

    it('should validate minimal form data', () => {
      const minimalForm = {
        long_url: 'https://example.com',
        base_domain: 'go2.reviews' as const,
      };
      expect(LinkCreationFormSchema.parse(minimalForm)).toEqual(minimalForm);
    });

    it('should reject empty URL', () => {
      const invalidForm = {
        long_url: '',
        base_domain: 'go2.video',
      };
      expect(() => LinkCreationFormSchema.parse(invalidForm)).toThrow('URL is required');
    });

    it('should reject invalid URL format', () => {
      const invalidForm = {
        long_url: 'not-a-url',
        base_domain: 'go2.video',
      };
      expect(() => LinkCreationFormSchema.parse(invalidForm)).toThrow('Please enter a valid URL');
    });

    it('should reject short custom code', () => {
      const invalidForm = {
        long_url: 'https://example.com',
        base_domain: 'go2.video',
        custom_code: 'ab',
      };
      expect(() => LinkCreationFormSchema.parse(invalidForm)).toThrow('at least 3 characters');
    });

    it('should reject long custom code', () => {
      const invalidForm = {
        long_url: 'https://example.com',
        base_domain: 'go2.video',
        custom_code: 'a'.repeat(51), // 51 characters
      };
      expect(() => LinkCreationFormSchema.parse(invalidForm)).toThrow('at most 50 characters');
    });

    it('should reject custom code with invalid characters', () => {
      const invalidForm = {
        long_url: 'https://example.com',
        base_domain: 'go2.video',
        custom_code: 'invalid@code!',
      };
      expect(() => LinkCreationFormSchema.parse(invalidForm)).toThrow('letters, numbers, hyphens, and underscores');
    });

    it('should reject short password', () => {
      const invalidForm = {
        long_url: 'https://example.com',
        base_domain: 'go2.video',
        password: '123',
      };
      expect(() => LinkCreationFormSchema.parse(invalidForm)).toThrow('at least 4 characters');
    });

    it('should reject long password', () => {
      const invalidForm = {
        long_url: 'https://example.com',
        base_domain: 'go2.video',
        password: 'a'.repeat(101), // 101 characters
      };
      expect(() => LinkCreationFormSchema.parse(invalidForm)).toThrow('at most 100 characters');
    });

    it('should reject past expiration date', () => {
      const invalidForm = {
        long_url: 'https://example.com',
        base_domain: 'go2.video',
        expires_at: new Date(Date.now() - 86400000), // Yesterday
      };
      expect(() => LinkCreationFormSchema.parse(invalidForm)).toThrow('must be in the future');
    });
  });

  describe('UserProfileFormSchema', () => {
    it('should validate valid user profile form', () => {
      const validForm = {
        display_name: 'John Doe',
        email: 'john@example.com',
      };
      expect(UserProfileFormSchema.parse(validForm)).toEqual(validForm);
    });

    it('should reject empty display name', () => {
      const invalidForm = {
        display_name: '',
        email: 'john@example.com',
      };
      expect(() => UserProfileFormSchema.parse(invalidForm)).toThrow('Display name is required');
    });

    it('should reject long display name', () => {
      const invalidForm = {
        display_name: 'a'.repeat(101), // 101 characters
        email: 'john@example.com',
      };
      expect(() => UserProfileFormSchema.parse(invalidForm)).toThrow('at most 100 characters');
    });

    it('should reject invalid email', () => {
      const invalidForm = {
        display_name: 'John Doe',
        email: 'invalid-email',
      };
      expect(() => UserProfileFormSchema.parse(invalidForm)).toThrow('valid email address');
    });

    it('should trim display name', () => {
      const formWithSpaces = {
        display_name: '  John Doe  ',
        email: 'john@example.com',
      };
      const result = UserProfileFormSchema.parse(formWithSpaces);
      expect(result.display_name).toBe('John Doe');
    });
  });

  describe('PasswordProtectionFormSchema', () => {
    it('should validate valid password form', () => {
      const validForm = {
        password: 'secret123',
      };
      expect(PasswordProtectionFormSchema.parse(validForm)).toEqual(validForm);
    });

    it('should reject empty password', () => {
      const invalidForm = {
        password: '',
      };
      expect(() => PasswordProtectionFormSchema.parse(invalidForm)).toThrow('Password is required');
    });

    it('should reject long password', () => {
      const invalidForm = {
        password: 'a'.repeat(101), // 101 characters
      };
      expect(() => PasswordProtectionFormSchema.parse(invalidForm)).toThrow('Password is too long');
    });
  });

  describe('AdminLinkUpdateFormSchema', () => {
    it('should validate valid admin update form', () => {
      const validForm = {
        disabled: true,
        expires_at: new Date(Date.now() + 86400000), // Tomorrow
        password: 'newsecret',
      };
      expect(AdminLinkUpdateFormSchema.parse(validForm)).toEqual(validForm);
    });

    it('should validate form with only some fields', () => {
      const partialForm = {
        disabled: false,
      };
      expect(AdminLinkUpdateFormSchema.parse(partialForm)).toEqual(partialForm);
    });

    it('should validate empty form', () => {
      const emptyForm = {};
      expect(AdminLinkUpdateFormSchema.parse(emptyForm)).toEqual(emptyForm);
    });

    it('should reject past expiration date', () => {
      const invalidForm = {
        expires_at: new Date(Date.now() - 86400000), // Yesterday
      };
      expect(() => AdminLinkUpdateFormSchema.parse(invalidForm)).toThrow('must be in the future');
    });

    it('should reject short password', () => {
      const invalidForm = {
        password: '123',
      };
      expect(() => AdminLinkUpdateFormSchema.parse(invalidForm)).toThrow('at least 4 characters');
    });
  });

  describe('DailyReportFormSchema', () => {
    it('should validate valid daily report form', () => {
      const yesterday = new Date(Date.now() - 86400000); // Yesterday
      const validForm = {
        date: yesterday,
        domain_filter: 'go2.video',
        email_recipients: ['admin@example.com', 'user@example.com'],
      };
      expect(DailyReportFormSchema.parse(validForm)).toEqual(validForm);
    });

    it('should validate minimal form', () => {
      const yesterday = new Date(Date.now() - 86400000); // Yesterday
      const minimalForm = {
        date: yesterday,
      };
      expect(DailyReportFormSchema.parse(minimalForm)).toEqual(minimalForm);
    });

    it('should reject future date', () => {
      const invalidForm = {
        date: new Date(Date.now() + 86400000), // Tomorrow
      };
      expect(() => DailyReportFormSchema.parse(invalidForm)).toThrow('cannot be in the future');
    });

    it('should reject invalid email in recipients', () => {
      const invalidForm = {
        date: new Date(),
        email_recipients: ['valid@example.com', 'invalid-email'],
      };
      expect(() => DailyReportFormSchema.parse(invalidForm)).toThrow('Invalid email address');
    });
  });

  describe('AnalyticsExportFormSchema', () => {
    it('should validate valid export form', () => {
      const validForm = {
        format: 'json' as const,
        period: '30d' as const,
      };
      expect(AnalyticsExportFormSchema.parse(validForm)).toEqual(validForm);
    });

    it('should validate CSV format', () => {
      const validForm = {
        format: 'csv' as const,
        period: 'all' as const,
      };
      expect(AnalyticsExportFormSchema.parse(validForm)).toEqual(validForm);
    });

    it('should reject invalid format', () => {
      const invalidForm = {
        format: 'xml',
        period: '7d',
      };
      expect(() => AnalyticsExportFormSchema.parse(invalidForm)).toThrow('JSON or CSV');
    });

    it('should reject invalid period', () => {
      const invalidForm = {
        format: 'json',
        period: '90d',
      };
      expect(() => AnalyticsExportFormSchema.parse(invalidForm)).toThrow('7 days, 30 days, or all time');
    });
  });
});

describe('Validation Utilities', () => {
  describe('validateForm', () => {
    it('should return success for valid data', () => {
      const validData = {
        long_url: 'https://example.com',
        base_domain: 'go2.video',
      };
      const result = validateForm(LinkCreationFormSchema, validData);
      
      expect(result.success).toBe(true);
      expect(result.data).toEqual(validData);
      expect(result.errors).toBeUndefined();
    });

    it('should return errors for invalid data', () => {
      const invalidData = {
        long_url: 'not-a-url',
        base_domain: 'invalid-domain',
      };
      const result = validateForm(LinkCreationFormSchema, invalidData);
      
      expect(result.success).toBe(false);
      expect(result.data).toBeUndefined();
      expect(result.errors).toBeDefined();
      expect(result.errors!['long_url']).toContain('valid URL');
      expect(result.errors!['base_domain']).toBeDefined();
    });

    it('should handle nested field errors', () => {
      const invalidData = {
        long_url: 'https://example.com',
        base_domain: 'go2.video',
        custom_code: 'ab', // Too short
      };
      const result = validateForm(LinkCreationFormSchema, invalidData);
      
      expect(result.success).toBe(false);
      expect(result.errors!['custom_code']).toContain('at least 3 characters');
    });
  });

  describe('validateField', () => {
    it('should return success for valid field value', () => {
      const result = validateField(LinkCreationFormSchema.shape.long_url, 'https://example.com');
      
      expect(result.success).toBe(true);
      expect(result.error).toBeUndefined();
    });

    it('should return error for invalid field value', () => {
      const result = validateField(LinkCreationFormSchema.shape.long_url, 'not-a-url');
      
      expect(result.success).toBe(false);
      expect(result.error).toContain('valid URL');
    });
  });

  describe('Pre-built validators', () => {
    describe('urlValidator', () => {
      it('should validate valid URLs', () => {
        expect(urlValidator('https://example.com').success).toBe(true);
        expect(urlValidator('http://test.org').success).toBe(true);
        expect(urlValidator('https://sub.domain.com/path?query=1').success).toBe(true);
      });

      it('should reject invalid URLs', () => {
        expect(urlValidator('not-a-url').success).toBe(false);
        expect(urlValidator('ftp://example.com').success).toBe(false);
        expect(urlValidator('').success).toBe(false);
      });
    });

    describe('emailValidator', () => {
      it('should validate valid emails', () => {
        expect(emailValidator('test@example.com').success).toBe(true);
        expect(emailValidator('user.name+tag@domain.co.uk').success).toBe(true);
      });

      it('should reject invalid emails', () => {
        expect(emailValidator('invalid-email').success).toBe(false);
        expect(emailValidator('test@').success).toBe(false);
        expect(emailValidator('@example.com').success).toBe(false);
      });
    });

    describe('customCodeValidator', () => {
      it('should validate valid custom codes', () => {
        expect(customCodeValidator('abc').success).toBe(true);
        expect(customCodeValidator('my-code').success).toBe(true);
        expect(customCodeValidator('code_123').success).toBe(true);
        expect(customCodeValidator('a'.repeat(50)).success).toBe(true); // Max length
      });

      it('should reject invalid custom codes', () => {
        expect(customCodeValidator('ab').success).toBe(false); // Too short
        expect(customCodeValidator('a'.repeat(51)).success).toBe(false); // Too long
        expect(customCodeValidator('invalid@code').success).toBe(false); // Invalid chars
        expect(customCodeValidator('code with spaces').success).toBe(false); // Spaces
      });
    });

    describe('passwordValidator', () => {
      it('should validate valid passwords', () => {
        expect(passwordValidator('1234').success).toBe(true); // Min length
        expect(passwordValidator('secret123').success).toBe(true);
        expect(passwordValidator('a'.repeat(100)).success).toBe(true); // Max length
      });

      it('should reject invalid passwords', () => {
        expect(passwordValidator('123').success).toBe(false); // Too short
        expect(passwordValidator('a'.repeat(101)).success).toBe(false); // Too long
        expect(passwordValidator('').success).toBe(false); // Empty
      });
    });
  });
});