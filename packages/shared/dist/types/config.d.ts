import { BaseDomain } from './link';
export interface SafetySettings {
    enable_safe_browsing: boolean;
    blacklist_domains: string[];
    blacklist_keywords: string[];
}
export interface PlanLimits {
    free: {
        custom_codes: number;
    };
    paid: {
        custom_codes: number;
    };
}
export interface ConfigDocument {
    base_domains: BaseDomain[];
    domain_suggestions: {
        [hostname: string]: BaseDomain;
    };
    safety_settings: SafetySettings;
    plan_limits: PlanLimits;
}
