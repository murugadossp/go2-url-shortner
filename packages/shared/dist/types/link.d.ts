export type BaseDomain = 'go2.video' | 'go2.reviews' | 'go2.tools';
export type PlanType = 'free' | 'paid';
export interface LinkMetadata {
    title?: string;
    host?: string;
    favicon_url?: string;
}
export interface LinkDocument {
    long_url: string;
    base_domain: BaseDomain;
    owner_uid: string | null;
    password_hash: string | null;
    expires_at: Date | null;
    disabled: boolean;
    created_at: Date;
    created_by_ip: string | null;
    metadata: LinkMetadata;
    plan_type: PlanType;
    is_custom_code: boolean;
}
export interface CreateLinkRequest {
    long_url: string;
    base_domain: BaseDomain;
    custom_code?: string;
    password?: string;
    expires_at?: Date;
}
export interface CreateLinkResponse {
    short_url: string;
    code: string;
    qr_url: string;
    long_url: string;
    base_domain: BaseDomain;
    expires_at?: Date;
}
