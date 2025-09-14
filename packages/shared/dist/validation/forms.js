"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.passwordValidator = exports.customCodeValidator = exports.emailValidator = exports.urlValidator = exports.createFieldValidator = exports.validateField = exports.validateForm = exports.AnalyticsExportFormSchema = exports.DailyReportFormSchema = exports.AdminLinkUpdateFormSchema = exports.PasswordProtectionFormSchema = exports.UserProfileFormSchema = exports.LinkCreationFormSchema = void 0;
const zod_1 = require("zod");
const schemas_1 = require("./schemas");
// Form-specific validation schemas with enhanced error messages
exports.LinkCreationFormSchema = schemas_1.CreateLinkRequestSchema.extend({
    long_url: zod_1.z.string()
        .min(1, 'URL is required')
        .url('Please enter a valid URL (including http:// or https://)'),
    base_domain: schemas_1.BaseDomainSchema,
    custom_code: zod_1.z.string()
        .optional()
        .refine((val) => {
        if (!val)
            return true; // Optional field
        return val.length >= 3;
    }, 'Custom code must be at least 3 characters')
        .refine((val) => {
        if (!val)
            return true;
        return val.length <= 50;
    }, 'Custom code must be at most 50 characters')
        .refine((val) => {
        if (!val)
            return true;
        return /^[a-zA-Z0-9_-]+$/.test(val);
    }, 'Custom code can only contain letters, numbers, hyphens, and underscores'),
    password: zod_1.z.string()
        .optional()
        .refine((val) => {
        if (!val)
            return true; // Optional field
        return val.length >= 4;
    }, 'Password must be at least 4 characters')
        .refine((val) => {
        if (!val)
            return true;
        return val.length <= 100;
    }, 'Password must be at most 100 characters'),
    expires_at: zod_1.z.date()
        .optional()
        .refine((val) => {
        if (!val)
            return true; // Optional field
        return val > new Date();
    }, 'Expiration date must be in the future'),
});
exports.UserProfileFormSchema = zod_1.z.object({
    display_name: zod_1.z.string()
        .min(1, 'Display name is required')
        .max(100, 'Display name must be at most 100 characters')
        .trim(),
    email: zod_1.z.string()
        .email('Please enter a valid email address')
        .readonly(), // Email is read-only in profile forms
});
exports.PasswordProtectionFormSchema = zod_1.z.object({
    password: zod_1.z.string()
        .min(1, 'Password is required')
        .max(100, 'Password is too long'),
});
exports.AdminLinkUpdateFormSchema = zod_1.z.object({
    disabled: zod_1.z.boolean().optional(),
    expires_at: zod_1.z.date()
        .optional()
        .refine((val) => {
        if (!val)
            return true;
        return val > new Date();
    }, 'Expiration date must be in the future'),
    password: zod_1.z.string()
        .optional()
        .refine((val) => {
        if (!val)
            return true;
        return val.length >= 4;
    }, 'Password must be at least 4 characters')
        .refine((val) => {
        if (!val)
            return true;
        return val.length <= 100;
    }, 'Password must be at most 100 characters'),
});
exports.DailyReportFormSchema = zod_1.z.object({
    date: zod_1.z.date()
        .max(new Date(), 'Date cannot be in the future'),
    domain_filter: zod_1.z.string().optional(),
    email_recipients: zod_1.z.array(zod_1.z.string().email('Invalid email address')).optional(),
});
exports.AnalyticsExportFormSchema = zod_1.z.object({
    format: zod_1.z.enum(['json', 'csv'], {
        errorMap: () => ({ message: 'Format must be either JSON or CSV' })
    }),
    period: zod_1.z.enum(['7d', '30d', 'all'], {
        errorMap: () => ({ message: 'Period must be 7 days, 30 days, or all time' })
    }),
});
// Form validation helper functions
const validateForm = (schema, data) => {
    try {
        const result = schema.parse(data);
        return { success: true, data: result };
    }
    catch (error) {
        if (error instanceof zod_1.z.ZodError) {
            const errors = {};
            error.errors.forEach((err) => {
                const path = err.path.join('.');
                errors[path] = err.message;
            });
            return { success: false, errors };
        }
        return { success: false, errors: { general: 'Validation failed' } };
    }
};
exports.validateForm = validateForm;
const validateField = (schema, value) => {
    try {
        schema.parse(value);
        return { success: true };
    }
    catch (error) {
        if (error instanceof zod_1.z.ZodError) {
            return { success: false, error: error.errors[0]?.message || 'Invalid value' };
        }
        return { success: false, error: 'Validation failed' };
    }
};
exports.validateField = validateField;
// Real-time validation helpers for form fields
const createFieldValidator = (schema) => {
    return (value) => (0, exports.validateField)(schema, value);
};
exports.createFieldValidator = createFieldValidator;
// Pre-built field validators
exports.urlValidator = (0, exports.createFieldValidator)(zod_1.z.string().url().refine((url) => {
    return url.startsWith('http://') || url.startsWith('https://');
}, 'URL must use HTTP or HTTPS protocol'));
exports.emailValidator = (0, exports.createFieldValidator)(zod_1.z.string().email());
exports.customCodeValidator = (0, exports.createFieldValidator)(zod_1.z.string().min(3).max(50).regex(/^[a-zA-Z0-9_-]+$/));
exports.passwordValidator = (0, exports.createFieldValidator)(zod_1.z.string().min(4).max(100));
