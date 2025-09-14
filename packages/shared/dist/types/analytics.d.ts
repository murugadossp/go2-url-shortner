export type DeviceType = 'mobile' | 'desktop' | 'tablet' | 'unknown';
export interface LocationData {
    country: string | null;
    country_code: string | null;
    region: string | null;
    city: string | null;
    timezone: string | null;
    latitude: number | null;
    longitude: number | null;
}
export interface ClickDocument {
    ts: Date;
    ip_hash: string | null;
    ua: string | null;
    referrer: string | null;
    location: LocationData;
    device_type: DeviceType;
    browser: string | null;
    os: string | null;
}
export interface LinkStats {
    total_clicks: number;
    clicks_by_day: {
        [date: string]: number;
    };
    top_referrers: {
        [referrer: string]: number;
    };
    top_devices: {
        [device: string]: number;
    };
    last_clicked: Date | null;
    geographic_stats: GeographicStats;
}
export interface GeographicStats {
    countries: {
        [country: string]: number;
    };
    cities: {
        [city: string]: number;
    };
    regions: {
        [region: string]: number;
    };
}
