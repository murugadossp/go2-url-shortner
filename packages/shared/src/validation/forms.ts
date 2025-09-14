import { z } from 'zod';
import { 
  CreateLinkRequestSchema, 
  BaseDomainSchema,
  UserDocumentSchema 
} from './schemas';

// Form-specific validation schemas with enhanced error messages

export const LinkCreationFormSchema = CreateLinkRequestSchema.extend({
  long_url: z.string()
    .min(1, 'URL is required')
    .url('Please enter a valid URL (including http:// or https://)'),
  base_domain: BaseDomainSchema,
  custom_code: z.string()
    .optional()
    .refine((val) => {
      if (!val) return true; // Optional field
      return val.length >= 3;
    }, 'Custom code must be at least 3 characters')
    .refine((val) => {
      if (!val) return true;
      return val.length <= 50;
    }, 'Custom code must be at most 50 characters')
    .refine((val) => {
      if (!val) return true;
      return /^[a-zA-Z0-9_-]+$/.test(val);
    }, 'Custom code can only contain letters, numbers, hyphens, and underscores'),
  password: z.string()
    .optional()
    .refine((val) => {
      if (!val) return true; // Optional field
      return val.length >= 4;
    }, 'Password must be at least 4 characters')
    .refine((val) => {
      if (!val) return true;
      return val.length <= 100;
    }, 'Password must be at most 100 characters'),
  expires_at: z.date()
    .optional()
    .refine((val) => {
      if (!val) return true; // Optional field
      return val > new Date();
    }, 'Expiration date must be in the future'),
});

export const UserProfileFormSchema = z.object({
  display_name: z.string()
    .min(1, 'Display name is required')
    .max(100, 'Display name must be at most 100 characters')
    .trim(),
  email: z.string()
    .email('Please enter a valid email address')
    .readonly(), // Email is read-only in profile forms
});

export const PasswordProtectionFormSchema = z.object({
  password: z.string()
    .min(1, 'Password is required')
    .max(100, 'Password is too long'),
});

export const AdminLinkUpdateFormSchema = z.object({
  disabled: z.boolean().optional(),
  expires_at: z.date()
    .optional()
    .refine((val) => {
      if (!val) return true;
      return val > new Date();
    }, 'Expiration date must be in the future'),
  password: z.string()
    .optional()
    .refine((val) => {
      if (!val) return true;
      return val.length >= 4;
    }, 'Password must be at least 4 characters')
    .refine((val) => {
      if (!val) return true;
      return val.length <= 100;
    }, 'Password must be at most 100 characters'),
});

export const DailyReportFormSchema = z.object({
  date: z.date()
    .max(new Date(), 'Date cannot be in the future'),
  domain_filter: z.string().optional(),
  email_recipients: z.array(z.string().email('Invalid email address')).optional(),
});

export const AnalyticsExportFormSchema = z.object({
  format: z.enum(['json', 'csv'], {
    errorMap: () => ({ message: 'Format must be either JSON or CSV' })
  }),
  period: z.enum(['7d', '30d', 'all'], {
    errorMap: () => ({ message: 'Period must be 7 days, 30 days, or all time' })
  }),
});

// Form validation helper functions
export const validateForm = <T>(schema: z.ZodSchema<T>, data: unknown): {
  success: boolean;
  data?: T;
  errors?: Record<string, string>;
} => {
  try {
    const result = schema.parse(data);
    return { success: true, data: result };
  } catch (error) {
    if (error instanceof z.ZodError) {
      const errors: Record<string, string> = {};
      error.errors.forEach((err) => {
        const path = err.path.join('.');
        errors[path] = err.message;
      });
      return { success: false, errors };
    }
    return { success: false, errors: { general: 'Validation failed' } };
  }
};

export const validateField = <T>(schema: z.ZodSchema<T>, value: unknown): {
  success: boolean;
  error?: string;
} => {
  try {
    schema.parse(value);
    return { success: true };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return { success: false, error: error.errors[0]?.message || 'Invalid value' };
    }
    return { success: false, error: 'Validation failed' };
  }
};

// Real-time validation helpers for form fields
export const createFieldValidator = <T>(schema: z.ZodSchema<T>) => {
  return (value: unknown) => validateField(schema, value);
};

// Pre-built field validators
export const urlValidator = createFieldValidator(
  z.string().url().refine((url) => {
    return url.startsWith('http://') || url.startsWith('https://');
  }, 'URL must use HTTP or HTTPS protocol')
);
export const emailValidator = createFieldValidator(z.string().email());
export const customCodeValidator = createFieldValidator(
  z.string().min(3).max(50).regex(/^[a-zA-Z0-9_-]+$/)
);
export const passwordValidator = createFieldValidator(
  z.string().min(4).max(100)
);

// Type exports for form data
export type LinkCreationFormData = z.infer<typeof LinkCreationFormSchema>;
export type UserProfileFormData = z.infer<typeof UserProfileFormSchema>;
export type PasswordProtectionFormData = z.infer<typeof PasswordProtectionFormSchema>;
export type AdminLinkUpdateFormData = z.infer<typeof AdminLinkUpdateFormSchema>;
export type DailyReportFormData = z.infer<typeof DailyReportFormSchema>;
export type AnalyticsExportFormData = z.infer<typeof AnalyticsExportFormSchema>;