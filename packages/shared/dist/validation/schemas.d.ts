import { z } from 'zod';
export declare const BaseDomainSchema: z.ZodEnum<["go2.video", "go2.reviews", "go2.tools"]>;
export declare const PlanTypeSchema: z.ZodEnum<["free", "paid"]>;
export declare const DeviceTypeSchema: z.ZodEnum<["mobile", "desktop", "tablet", "unknown"]>;
export declare const LinkMetadataSchema: z.ZodObject<{
    title: z.ZodOptional<z.ZodString>;
    host: z.ZodOptional<z.ZodString>;
    favicon_url: z.ZodOptional<z.ZodString>;
}, "strip", z.ZodTypeAny, {
    title?: string | undefined;
    host?: string | undefined;
    favicon_url?: string | undefined;
}, {
    title?: string | undefined;
    host?: string | undefined;
    favicon_url?: string | undefined;
}>;
export declare const LocationDataSchema: z.ZodObject<{
    country: z.ZodNullable<z.ZodString>;
    country_code: z.ZodNullable<z.ZodString>;
    region: z.ZodNullable<z.ZodString>;
    city: z.ZodNullable<z.ZodString>;
    timezone: z.ZodNullable<z.ZodString>;
    latitude: z.ZodNullable<z.ZodNumber>;
    longitude: z.ZodNullable<z.ZodNumber>;
}, "strip", z.ZodTypeAny, {
    country: string | null;
    country_code: string | null;
    region: string | null;
    city: string | null;
    timezone: string | null;
    latitude: number | null;
    longitude: number | null;
}, {
    country: string | null;
    country_code: string | null;
    region: string | null;
    city: string | null;
    timezone: string | null;
    latitude: number | null;
    longitude: number | null;
}>;
export declare const LinkDocumentSchema: z.ZodObject<{
    long_url: z.ZodString;
    base_domain: z.ZodEnum<["go2.video", "go2.reviews", "go2.tools"]>;
    owner_uid: z.ZodNullable<z.ZodString>;
    password_hash: z.ZodNullable<z.ZodString>;
    expires_at: z.ZodNullable<z.ZodDate>;
    disabled: z.ZodBoolean;
    created_at: z.ZodDate;
    created_by_ip: z.ZodNullable<z.ZodString>;
    metadata: z.ZodObject<{
        title: z.ZodOptional<z.ZodString>;
        host: z.ZodOptional<z.ZodString>;
        favicon_url: z.ZodOptional<z.ZodString>;
    }, "strip", z.ZodTypeAny, {
        title?: string | undefined;
        host?: string | undefined;
        favicon_url?: string | undefined;
    }, {
        title?: string | undefined;
        host?: string | undefined;
        favicon_url?: string | undefined;
    }>;
    plan_type: z.ZodEnum<["free", "paid"]>;
    is_custom_code: z.ZodBoolean;
}, "strip", z.ZodTypeAny, {
    long_url: string;
    base_domain: "go2.video" | "go2.reviews" | "go2.tools";
    owner_uid: string | null;
    password_hash: string | null;
    expires_at: Date | null;
    disabled: boolean;
    created_at: Date;
    created_by_ip: string | null;
    metadata: {
        title?: string | undefined;
        host?: string | undefined;
        favicon_url?: string | undefined;
    };
    plan_type: "free" | "paid";
    is_custom_code: boolean;
}, {
    long_url: string;
    base_domain: "go2.video" | "go2.reviews" | "go2.tools";
    owner_uid: string | null;
    password_hash: string | null;
    expires_at: Date | null;
    disabled: boolean;
    created_at: Date;
    created_by_ip: string | null;
    metadata: {
        title?: string | undefined;
        host?: string | undefined;
        favicon_url?: string | undefined;
    };
    plan_type: "free" | "paid";
    is_custom_code: boolean;
}>;
export declare const ClickDocumentSchema: z.ZodObject<{
    ts: z.ZodDate;
    ip_hash: z.ZodNullable<z.ZodString>;
    ua: z.ZodNullable<z.ZodString>;
    referrer: z.ZodNullable<z.ZodString>;
    location: z.ZodObject<{
        country: z.ZodNullable<z.ZodString>;
        country_code: z.ZodNullable<z.ZodString>;
        region: z.ZodNullable<z.ZodString>;
        city: z.ZodNullable<z.ZodString>;
        timezone: z.ZodNullable<z.ZodString>;
        latitude: z.ZodNullable<z.ZodNumber>;
        longitude: z.ZodNullable<z.ZodNumber>;
    }, "strip", z.ZodTypeAny, {
        country: string | null;
        country_code: string | null;
        region: string | null;
        city: string | null;
        timezone: string | null;
        latitude: number | null;
        longitude: number | null;
    }, {
        country: string | null;
        country_code: string | null;
        region: string | null;
        city: string | null;
        timezone: string | null;
        latitude: number | null;
        longitude: number | null;
    }>;
    device_type: z.ZodEnum<["mobile", "desktop", "tablet", "unknown"]>;
    browser: z.ZodNullable<z.ZodString>;
    os: z.ZodNullable<z.ZodString>;
}, "strip", z.ZodTypeAny, {
    ts: Date;
    ip_hash: string | null;
    ua: string | null;
    referrer: string | null;
    location: {
        country: string | null;
        country_code: string | null;
        region: string | null;
        city: string | null;
        timezone: string | null;
        latitude: number | null;
        longitude: number | null;
    };
    device_type: "mobile" | "desktop" | "tablet" | "unknown";
    browser: string | null;
    os: string | null;
}, {
    ts: Date;
    ip_hash: string | null;
    ua: string | null;
    referrer: string | null;
    location: {
        country: string | null;
        country_code: string | null;
        region: string | null;
        city: string | null;
        timezone: string | null;
        latitude: number | null;
        longitude: number | null;
    };
    device_type: "mobile" | "desktop" | "tablet" | "unknown";
    browser: string | null;
    os: string | null;
}>;
export declare const UserDocumentSchema: z.ZodObject<{
    email: z.ZodString;
    display_name: z.ZodString;
    plan_type: z.ZodEnum<["free", "paid"]>;
    custom_codes_used: z.ZodNumber;
    custom_codes_reset_date: z.ZodDate;
    created_at: z.ZodDate;
    last_login: z.ZodDate;
    is_admin: z.ZodBoolean;
}, "strip", z.ZodTypeAny, {
    created_at: Date;
    plan_type: "free" | "paid";
    email: string;
    display_name: string;
    custom_codes_used: number;
    custom_codes_reset_date: Date;
    last_login: Date;
    is_admin: boolean;
}, {
    created_at: Date;
    plan_type: "free" | "paid";
    email: string;
    display_name: string;
    custom_codes_used: number;
    custom_codes_reset_date: Date;
    last_login: Date;
    is_admin: boolean;
}>;
export declare const CreateLinkRequestSchema: z.ZodObject<{
    long_url: z.ZodString;
    base_domain: z.ZodEnum<["go2.video", "go2.reviews", "go2.tools"]>;
    custom_code: z.ZodOptional<z.ZodString>;
    password: z.ZodOptional<z.ZodString>;
    expires_at: z.ZodOptional<z.ZodDate>;
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
export declare const CreateLinkResponseSchema: z.ZodObject<{
    short_url: z.ZodString;
    code: z.ZodString;
    qr_url: z.ZodString;
    long_url: z.ZodString;
    base_domain: z.ZodEnum<["go2.video", "go2.reviews", "go2.tools"]>;
    expires_at: z.ZodOptional<z.ZodDate>;
}, "strip", z.ZodTypeAny, {
    code: string;
    long_url: string;
    base_domain: "go2.video" | "go2.reviews" | "go2.tools";
    short_url: string;
    qr_url: string;
    expires_at?: Date | undefined;
}, {
    code: string;
    long_url: string;
    base_domain: "go2.video" | "go2.reviews" | "go2.tools";
    short_url: string;
    qr_url: string;
    expires_at?: Date | undefined;
}>;
export declare const SafetySettingsSchema: z.ZodObject<{
    enable_safe_browsing: z.ZodBoolean;
    blacklist_domains: z.ZodArray<z.ZodString, "many">;
    blacklist_keywords: z.ZodArray<z.ZodString, "many">;
}, "strip", z.ZodTypeAny, {
    enable_safe_browsing: boolean;
    blacklist_domains: string[];
    blacklist_keywords: string[];
}, {
    enable_safe_browsing: boolean;
    blacklist_domains: string[];
    blacklist_keywords: string[];
}>;
export declare const PlanLimitsSchema: z.ZodObject<{
    free: z.ZodObject<{
        custom_codes: z.ZodNumber;
    }, "strip", z.ZodTypeAny, {
        custom_codes: number;
    }, {
        custom_codes: number;
    }>;
    paid: z.ZodObject<{
        custom_codes: z.ZodNumber;
    }, "strip", z.ZodTypeAny, {
        custom_codes: number;
    }, {
        custom_codes: number;
    }>;
}, "strip", z.ZodTypeAny, {
    free: {
        custom_codes: number;
    };
    paid: {
        custom_codes: number;
    };
}, {
    free: {
        custom_codes: number;
    };
    paid: {
        custom_codes: number;
    };
}>;
export declare const ConfigDocumentSchema: z.ZodObject<{
    base_domains: z.ZodArray<z.ZodEnum<["go2.video", "go2.reviews", "go2.tools"]>, "many">;
    domain_suggestions: z.ZodRecord<z.ZodString, z.ZodEnum<["go2.video", "go2.reviews", "go2.tools"]>>;
    safety_settings: z.ZodObject<{
        enable_safe_browsing: z.ZodBoolean;
        blacklist_domains: z.ZodArray<z.ZodString, "many">;
        blacklist_keywords: z.ZodArray<z.ZodString, "many">;
    }, "strip", z.ZodTypeAny, {
        enable_safe_browsing: boolean;
        blacklist_domains: string[];
        blacklist_keywords: string[];
    }, {
        enable_safe_browsing: boolean;
        blacklist_domains: string[];
        blacklist_keywords: string[];
    }>;
    plan_limits: z.ZodObject<{
        free: z.ZodObject<{
            custom_codes: z.ZodNumber;
        }, "strip", z.ZodTypeAny, {
            custom_codes: number;
        }, {
            custom_codes: number;
        }>;
        paid: z.ZodObject<{
            custom_codes: z.ZodNumber;
        }, "strip", z.ZodTypeAny, {
            custom_codes: number;
        }, {
            custom_codes: number;
        }>;
    }, "strip", z.ZodTypeAny, {
        free: {
            custom_codes: number;
        };
        paid: {
            custom_codes: number;
        };
    }, {
        free: {
            custom_codes: number;
        };
        paid: {
            custom_codes: number;
        };
    }>;
}, "strip", z.ZodTypeAny, {
    base_domains: ("go2.video" | "go2.reviews" | "go2.tools")[];
    domain_suggestions: Record<string, "go2.video" | "go2.reviews" | "go2.tools">;
    safety_settings: {
        enable_safe_browsing: boolean;
        blacklist_domains: string[];
        blacklist_keywords: string[];
    };
    plan_limits: {
        free: {
            custom_codes: number;
        };
        paid: {
            custom_codes: number;
        };
    };
}, {
    base_domains: ("go2.video" | "go2.reviews" | "go2.tools")[];
    domain_suggestions: Record<string, "go2.video" | "go2.reviews" | "go2.tools">;
    safety_settings: {
        enable_safe_browsing: boolean;
        blacklist_domains: string[];
        blacklist_keywords: string[];
    };
    plan_limits: {
        free: {
            custom_codes: number;
        };
        paid: {
            custom_codes: number;
        };
    };
}>;
export declare const ErrorResponseSchema: z.ZodObject<{
    error: z.ZodObject<{
        code: z.ZodString;
        message: z.ZodString;
        details: z.ZodOptional<z.ZodAny>;
    }, "strip", z.ZodTypeAny, {
        code: string;
        message: string;
        details?: any;
    }, {
        code: string;
        message: string;
        details?: any;
    }>;
}, "strip", z.ZodTypeAny, {
    error: {
        code: string;
        message: string;
        details?: any;
    };
}, {
    error: {
        code: string;
        message: string;
        details?: any;
    };
}>;
export declare const SuccessResponseSchema: z.ZodObject<{
    data: z.ZodAny;
    message: z.ZodOptional<z.ZodString>;
}, "strip", z.ZodTypeAny, {
    message?: string | undefined;
    data?: any;
}, {
    message?: string | undefined;
    data?: any;
}>;
export type LinkDocumentInput = z.input<typeof LinkDocumentSchema>;
export type ClickDocumentInput = z.input<typeof ClickDocumentSchema>;
export type UserDocumentInput = z.input<typeof UserDocumentSchema>;
export type CreateLinkRequestInput = z.input<typeof CreateLinkRequestSchema>;
export type CreateLinkResponseInput = z.input<typeof CreateLinkResponseSchema>;
export type ConfigDocumentInput = z.input<typeof ConfigDocumentSchema>;
