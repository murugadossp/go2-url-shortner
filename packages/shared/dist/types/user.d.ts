import { PlanType } from './link';
export interface UserDocument {
    email: string;
    display_name: string;
    plan_type: PlanType;
    custom_codes_used: number;
    custom_codes_reset_date: Date;
    created_at: Date;
    last_login: Date;
    is_admin: boolean;
}
