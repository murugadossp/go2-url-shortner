import { z } from 'zod';
export declare const LinkCreationFormSchema: z.ZodObject<{} & {
    long_url: z.ZodString;
    base_domain: z.ZodEnum<["go2.video", "go2.reviews", "go2.tools"]>;
    custom_code: z.ZodEffects<z.ZodEffects<z.ZodEffects<z.ZodOptional<z.ZodString>, string | undefined, string | undefined>, string | undefined, string | undefined>, string | undefined, string | undefined>;
    password: z.ZodEffects<z.ZodEffects<z.ZodOptional<z.ZodString>, string | undefined, string | undefined>, string | undefined, string | undefined>;
    expires_at: z.ZodEffects<z.ZodOptional<z.ZodDate>, Date | undefined, Date | undefined>;
}, "strip", z.ZodTypeAny, {
    long_url: string;
    base_domain: "go2.video" | "go2.reviews" | "go2.tools";
    expires_at?: Date | undefined;
    custom_code?: string | undefined;
    password?: string | undefined;
}, {
    long_url: string;
    base_domain: "go2.video" | "go2.reviews" | "go2.tools";
    expires_at?: Date | undefined;
    custom_code?: string | undefined;
    password?: string | undefined;
}>;
export declare const UserProfileFormSchema: z.ZodObject<{
    display_name: z.ZodString;
    email: z.ZodReadonly<z.ZodString>;
}, "strip", z.ZodTypeAny, {
    email: string;
    display_name: string;
}, {
    email: string;
    display_name: string;
}>;
export declare const PasswordProtectionFormSchema: z.ZodObject<{
    password: z.ZodString;
}, "strip", z.ZodTypeAny, {
    password: string;
}, {
    password: string;
}>;
export declare const AdminLinkUpdateFormSchema: z.ZodObject<{
    disabled: z.ZodOptional<z.ZodBoolean>;
    expires_at: z.ZodEffects<z.ZodOptional<z.ZodDate>, Date | undefined, Date | undefined>;
    password: z.ZodEffects<z.ZodEffects<z.ZodOptional<z.ZodString>, string | undefined, string | undefined>, string | undefined, string | undefined>;
}, "strip", z.ZodTypeAny, {
    expires_at?: Date | undefined;
    disabled?: boolean | undefined;
    password?: string | undefined;
}, {
    expires_at?: Date | undefined;
    disabled?: boolean | undefined;
    password?: string | undefined;
}>;
export declare const DailyReportFormSchema: z.ZodObject<{
    date: z.ZodDate;
    domain_filter: z.ZodOptional<z.ZodString>;
    email_recipients: z.ZodOptional<z.ZodArray<z.ZodString, "many">>;
}, "strip", z.ZodTypeAny, {
    date: Date;
    domain_filter?: string | undefined;
    email_recipients?: string[] | undefined;
}, {
    date: Date;
    domain_filter?: string | undefined;
    email_recipients?: string[] | undefined;
}>;
export declare const AnalyticsExportFormSchema: z.ZodObject<{
    format: z.ZodEnum<["json", "csv"]>;
    period: z.ZodEnum<["7d", "30d", "all"]>;
}, "strip", z.ZodTypeAny, {
    format: "json" | "csv";
    period: "7d" | "30d" | "all";
}, {
    format: "json" | "csv";
    period: "7d" | "30d" | "all";
}>;
export declare const validateForm: <T>(schema: z.ZodSchema<T>, data: unknown) => {
    success: boolean;
    data?: T;
    errors?: Record<string, string>;
};
export declare const validateField: <T>(schema: z.ZodSchema<T>, value: unknown) => {
    success: boolean;
    error?: string;
};
export declare const createFieldValidator: <T>(schema: z.ZodSchema<T>) => (value: unknown) => {
    success: boolean;
    error?: string;
};
export declare const urlValidator: (value: unknown) => {
    success: boolean;
    error?: string;
};
export declare const emailValidator: (value: unknown) => {
    success: boolean;
    error?: string;
};
export declare const customCodeValidator: (value: unknown) => {
    success: boolean;
    error?: string;
};
export declare const passwordValidator: (value: unknown) => {
    success: boolean;
    error?: string;
};
export type LinkCreationFormData = z.infer<typeof LinkCreationFormSchema>;
export type UserProfileFormData = z.infer<typeof UserProfileFormSchema>;
export type PasswordProtectionFormData = z.infer<typeof PasswordProtectionFormSchema>;
export type AdminLinkUpdateFormData = z.infer<typeof AdminLinkUpdateFormSchema>;
export type DailyReportFormData = z.infer<typeof DailyReportFormSchema>;
export type AnalyticsExportFormData = z.infer<typeof AnalyticsExportFormSchema>;
