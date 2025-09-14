import { z } from 'zod';

// Base domain validation
export const BaseDomainSchema = z.enum(['go2.video', 'go2.reviews', 'go2.tools']);

// Plan type validation
export const PlanTypeSchema = z.enum(['free', 'paid']);

// Device type validation
export const DeviceTypeSchema = z.enum(['mobile', 'desktop', 'tablet', 'unknown']);

// Link metadata validation
export const LinkMetadataSchema = z.object({
  title: z.string().optional(),
  host: z.string().optional(),
  favicon_url: z.string().url().optional(),
});

// Location data validation
export const LocationDataSchema = z.object({
  country: z.string().nullable(),
  country_code: z.string().length(2).nullable(),
  region: z.string().nullable(),
  city: z.string().nullable(),
  timezone: z.string().nullable(),
  latitude: z.number().min(-90).max(90).nullable(),
  longitude: z.number().min(-180).max(180).nullable(),
});

// Link document validation
export const LinkDocumentSchema = z.object({
  long_url: z.string().url('Invalid URL format'),
  base_domain: BaseDomainSchema,
  owner_uid: z.string().nullable(),
  password_hash: z.string().nullable(),
  expires_at: z.date().nullable(),
  disabled: z.boolean(),
  created_at: z.date(),
  created_by_ip: z.string().nullable(),
  metadata: LinkMetadataSchema,
  plan_type: PlanTypeSchema,
  is_custom_code: z.boolean(),
});

// Click document validation
export const ClickDocumentSchema = z.object({
  ts: z.date(),
  ip_hash: z.string().nullable(),
  ua: z.string().nullable(),
  referrer: z.string().nullable(),
  location: LocationDataSchema,
  device_type: DeviceTypeSchema,
  browser: z.string().nullable(),
  os: z.string().nullable(),
});

// User document validation
export const UserDocumentSchema = z.object({
  email: z.string().email('Invalid email format'),
  display_name: z.string().min(1, 'Display name is required'),
  plan_type: PlanTypeSchema,
  custom_codes_used: z.number().min(0),
  custom_codes_reset_date: z.date(),
  created_at: z.date(),
  last_login: z.date(),
  is_admin: z.boolean(),
});

// Create link request validation
export const CreateLinkRequestSchema = z.object({
  long_url: z.string().url('Invalid URL format'),
  base_domain: BaseDomainSchema,
  custom_code: z.string()
    .min(3, 'Custom code must be at least 3 characters')
    .max(50, 'Custom code must be at most 50 characters')
    .regex(/^[a-zA-Z0-9_-]+$/, 'Custom code can only contain letters, numbers, hyphens, and underscores')
    .optional(),
  password: z.string()
    .min(4, 'Password must be at least 4 characters')
    .max(100, 'Password must be at most 100 characters')
    .optional(),
  expires_at: z.date().min(new Date(), 'Expiration date must be in the future').optional(),
});

// Create link response validation
export const CreateLinkResponseSchema = z.object({
  short_url: z.string().url(),
  code: z.string(),
  qr_url: z.string().url(),
  long_url: z.string().url(),
  base_domain: BaseDomainSchema,
  expires_at: z.date().optional(),
});

// Safety settings validation
export const SafetySettingsSchema = z.object({
  enable_safe_browsing: z.boolean(),
  blacklist_domains: z.array(z.string()),
  blacklist_keywords: z.array(z.string()),
});

// Plan limits validation
export const PlanLimitsSchema = z.object({
  free: z.object({ custom_codes: z.number().min(0) }),
  paid: z.object({ custom_codes: z.number().min(0) }),
});

// Config document validation
export const ConfigDocumentSchema = z.object({
  base_domains: z.array(BaseDomainSchema),
  domain_suggestions: z.record(z.string(), BaseDomainSchema),
  safety_settings: SafetySettingsSchema,
  plan_limits: PlanLimitsSchema,
});

// Error response validation
export const ErrorResponseSchema = z.object({
  error: z.object({
    code: z.string(),
    message: z.string(),
    details: z.any().optional(),
  }),
});

// Success response validation
export const SuccessResponseSchema = z.object({
  data: z.any(),
  message: z.string().optional(),
});

// Export type inference helpers
export type LinkDocumentInput = z.input<typeof LinkDocumentSchema>;
export type ClickDocumentInput = z.input<typeof ClickDocumentSchema>;
export type UserDocumentInput = z.input<typeof UserDocumentSchema>;
export type CreateLinkRequestInput = z.input<typeof CreateLinkRequestSchema>;
export type CreateLinkResponseInput = z.input<typeof CreateLinkResponseSchema>;
export type ConfigDocumentInput = z.input<typeof ConfigDocumentSchema>;