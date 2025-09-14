"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SuccessResponseSchema = exports.ErrorResponseSchema = exports.ConfigDocumentSchema = exports.PlanLimitsSchema = exports.SafetySettingsSchema = exports.CreateLinkResponseSchema = exports.CreateLinkRequestSchema = exports.UserDocumentSchema = exports.ClickDocumentSchema = exports.LinkDocumentSchema = exports.LocationDataSchema = exports.LinkMetadataSchema = exports.DeviceTypeSchema = exports.PlanTypeSchema = exports.BaseDomainSchema = void 0;
const zod_1 = require("zod");
// Base domain validation
exports.BaseDomainSchema = zod_1.z.enum(['go2.video', 'go2.reviews', 'go2.tools']);
// Plan type validation
exports.PlanTypeSchema = zod_1.z.enum(['free', 'paid']);
// Device type validation
exports.DeviceTypeSchema = zod_1.z.enum(['mobile', 'desktop', 'tablet', 'unknown']);
// Link metadata validation
exports.LinkMetadataSchema = zod_1.z.object({
    title: zod_1.z.string().optional(),
    host: zod_1.z.string().optional(),
    favicon_url: zod_1.z.string().url().optional(),
});
// Location data validation
exports.LocationDataSchema = zod_1.z.object({
    country: zod_1.z.string().nullable(),
    country_code: zod_1.z.string().length(2).nullable(),
    region: zod_1.z.string().nullable(),
    city: zod_1.z.string().nullable(),
    timezone: zod_1.z.string().nullable(),
    latitude: zod_1.z.number().min(-90).max(90).nullable(),
    longitude: zod_1.z.number().min(-180).max(180).nullable(),
});
// Link document validation
exports.LinkDocumentSchema = zod_1.z.object({
    long_url: zod_1.z.string().url('Invalid URL format'),
    base_domain: exports.BaseDomainSchema,
    owner_uid: zod_1.z.string().nullable(),
    password_hash: zod_1.z.string().nullable(),
    expires_at: zod_1.z.date().nullable(),
    disabled: zod_1.z.boolean(),
    created_at: zod_1.z.date(),
    created_by_ip: zod_1.z.string().nullable(),
    metadata: exports.LinkMetadataSchema,
    plan_type: exports.PlanTypeSchema,
    is_custom_code: zod_1.z.boolean(),
});
// Click document validation
exports.ClickDocumentSchema = zod_1.z.object({
    ts: zod_1.z.date(),
    ip_hash: zod_1.z.string().nullable(),
    ua: zod_1.z.string().nullable(),
    referrer: zod_1.z.string().nullable(),
    location: exports.LocationDataSchema,
    device_type: exports.DeviceTypeSchema,
    browser: zod_1.z.string().nullable(),
    os: zod_1.z.string().nullable(),
});
// User document validation
exports.UserDocumentSchema = zod_1.z.object({
    email: zod_1.z.string().email('Invalid email format'),
    display_name: zod_1.z.string().min(1, 'Display name is required'),
    plan_type: exports.PlanTypeSchema,
    custom_codes_used: zod_1.z.number().min(0),
    custom_codes_reset_date: zod_1.z.date(),
    created_at: zod_1.z.date(),
    last_login: zod_1.z.date(),
    is_admin: zod_1.z.boolean(),
});
// Create link request validation
exports.CreateLinkRequestSchema = zod_1.z.object({
    long_url: zod_1.z.string().url('Invalid URL format'),
    base_domain: exports.BaseDomainSchema,
    custom_code: zod_1.z.string()
        .min(3, 'Custom code must be at least 3 characters')
        .max(50, 'Custom code must be at most 50 characters')
        .regex(/^[a-zA-Z0-9_-]+$/, 'Custom code can only contain letters, numbers, hyphens, and underscores')
        .optional(),
    password: zod_1.z.string()
        .min(4, 'Password must be at least 4 characters')
        .max(100, 'Password must be at most 100 characters')
        .optional(),
    expires_at: zod_1.z.date().min(new Date(), 'Expiration date must be in the future').optional(),
});
// Create link response validation
exports.CreateLinkResponseSchema = zod_1.z.object({
    short_url: zod_1.z.string().url(),
    code: zod_1.z.string(),
    qr_url: zod_1.z.string().url(),
    long_url: zod_1.z.string().url(),
    base_domain: exports.BaseDomainSchema,
    expires_at: zod_1.z.date().optional(),
});
// Safety settings validation
exports.SafetySettingsSchema = zod_1.z.object({
    enable_safe_browsing: zod_1.z.boolean(),
    blacklist_domains: zod_1.z.array(zod_1.z.string()),
    blacklist_keywords: zod_1.z.array(zod_1.z.string()),
});
// Plan limits validation
exports.PlanLimitsSchema = zod_1.z.object({
    free: zod_1.z.object({ custom_codes: zod_1.z.number().min(0) }),
    paid: zod_1.z.object({ custom_codes: zod_1.z.number().min(0) }),
});
// Config document validation
exports.ConfigDocumentSchema = zod_1.z.object({
    base_domains: zod_1.z.array(exports.BaseDomainSchema),
    domain_suggestions: zod_1.z.record(zod_1.z.string(), exports.BaseDomainSchema),
    safety_settings: exports.SafetySettingsSchema,
    plan_limits: exports.PlanLimitsSchema,
});
// Error response validation
exports.ErrorResponseSchema = zod_1.z.object({
    error: zod_1.z.object({
        code: zod_1.z.string(),
        message: zod_1.z.string(),
        details: zod_1.z.any().optional(),
    }),
});
// Success response validation
exports.SuccessResponseSchema = zod_1.z.object({
    data: zod_1.z.any(),
    message: zod_1.z.string().optional(),
});
