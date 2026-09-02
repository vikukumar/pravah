export type RoleType = 'super_admin' | 'admin' | 'moderator' | 'support' | 'org_owner' | 'org_admin' | 'manager' | 'editor' | 'publisher' | 'analyst' | 'user' | 'custom';

export type ContentStatus = 'draft' | 'ai_generated' | 'review' | 'approved' | 'scheduled' | 'publishing' | 'published' | 'failed' | 'cancelled' | 'rejected' | 'archived';

export type PlatformType = 'facebook' | 'instagram' | 'x' | 'linkedin' | 'youtube';

export type WorkflowStatus = 'draft' | 'published' | 'archived' | 'disabled';

export type WorkflowExecutionStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export type SubscriptionStatus = 'trial' | 'active' | 'past_due' | 'grace_period' | 'cancelled' | 'expired' | 'suspended';

export type PaymentStatus = 'created' | 'pending' | 'paid' | 'failed' | 'cancelled' | 'refunded' | 'partially_refunded' | 'expired';

export type PaymentGateway = 'razorpay' | 'cashfree';

export interface UserProfile {
  id: string;
  email: string;
  firstName?: string;
  first_name?: string;
  middleName?: string | null;
  middle_name?: string | null;
  lastName?: string | null;
  last_name?: string | null;
  phone?: string | null;
  avatarUrl?: string | null;
  avatar_url?: string | null;
  isSuperAdmin?: boolean;
  is_super_admin?: boolean;
  isActive?: boolean;
  is_active?: boolean;
  isVerified?: boolean;
  is_verified?: boolean;
  twoFactorEnabled?: boolean;
  two_factor_enabled?: boolean;
  createdAt?: string;
  created_at?: string;
  updatedAt?: string;
  updated_at?: string;
}

export interface Organisation {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  logoUrl?: string | null;
  logo_url?: string | null;
  website?: string | null;
  industry?: string | null;
  timezone: string;
  locale: string;
  brandIdentity?: any;
  brand_identity?: any;
  userRole?: string;
  user_role?: string;
  publishingPaused?: boolean;
  publishing_paused?: boolean;
  workflowsPaused?: boolean;
  workflows_paused?: boolean;
  automationDisabled?: boolean;
  automation_disabled?: boolean;
  createdAt?: string;
  created_at?: string;
  updatedAt?: string;
  updated_at?: string;
}

export interface Member {
  id: string;
  organisation_id?: string;
  organisationId?: string;
  user_id?: string;
  userId?: string;
  email?: string;
  user_email?: string;
  userEmail?: string;
  first_name?: string;
  last_name?: string | null;
  user_name?: string;
  role_id: string;
  roleId?: string;
  role_name: string;
  roleName?: string;
  is_active?: boolean;
  avatar_url?: string | null;
  created_at?: string;
  createdAt?: string;
}

export interface OrganisationMember {
  id: string;
  organisationId?: string;
  organisation_id?: string;
  userId?: string;
  user_id?: string;
  roleId?: string;
  role_id?: string;
  roleName?: string;
  role_name?: string;
  user?: UserProfile;
  created_at?: string;
}

export interface Role {
  id: string;
  name: string;
  display_name: string;
  description?: string | null;
  is_system?: boolean;
  permissions?: string[];
}

export interface SocialProvider {
  id: string;
  name: string;
  display_name: string;
  icon_url?: string | null;
  is_enabled: boolean;
  supports_text: boolean;
  supports_image: boolean;
  supports_video: boolean;
  supports_carousel: boolean;
  supports_pages: boolean;
  supports_analytics: boolean;
  supports_scheduling: boolean;
  supports_comments: boolean;
  max_char_limit: number;
}

export interface SocialAccount {
  id: string;
  organisation_id?: string;
  organisationId?: string;
  provider: string;
  account_id?: string;
  accountId?: string;
  account_name?: string;
  accountName?: string;
  username?: string | null;
  profile_image_url?: string | null;
  profileImageUrl?: string | null;
  is_connected?: boolean;
  isConnected?: boolean;
  health_status?: string;
  healthStatus?: string;
  last_sync_at?: string | null;
  lastSyncAt?: string | null;
  created_at?: string;
  createdAt?: string;
}

export interface SocialPage {
  id: string;
  social_account_id?: string;
  socialAccountId?: string;
  organisation_id?: string;
  organisationId?: string;
  platform: string;
  page_id?: string;
  pageId?: string;
  name: string;
  username?: string | null;
  page_url?: string | null;
  pageUrl?: string | null;
  profile_image_url?: string | null;
  profileImageUrl?: string | null;
  is_connected?: boolean;
  isConnected?: boolean;
  created_at?: string;
}

export interface SocialProfileSummary {
  id: string;
  social_account_id?: string;
  version: number;
  brand_identity: string;
  business_category: string;
  description: string;
  audience_signals: string[];
  content_themes: string[];
  tone: string;
  keywords: string[];
  hashtags: string[];
  posting_patterns: string;
  content_formats: string[];
  engagement_patterns: string;
  created_at: string;
}

export interface ContentPost {
  id: string;
  organisation_id?: string;
  campaign_id?: string | null;
  title?: string | null;
  body: string;
  platforms: string[];
  account_ids?: string[];
  page_ids?: string[];
  media_urls?: string[];
  status: string;
  scheduled_at?: string | null;
  published_at?: string | null;
  approval_required?: boolean;
  current_approver_id?: string | null;
  ai_provider_id?: string | null;
  ai_model?: string | null;
  ai_prompt?: string | null;
  version?: number;
  created_at?: string;
  updated_at?: string;
}

export interface Plan {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  price_monthly?: number;
  priceMonthly?: number;
  price_yearly?: number;
  priceYearly?: number;
  currency: string;
  is_free?: boolean;
  isFree?: boolean;
  is_active?: boolean;
  isActive?: boolean;
  trial_days?: number;
  trialDays?: number;
  features?: {
    social_account_limit?: number;
    socialAccountLimit?: number;
    page_limit?: number;
    pageLimit?: number;
    daily_post_limit?: number;
    dailyPostLimit?: number;
    monthly_post_limit?: number;
    monthlyPostLimit?: number;
    ai_token_limit_monthly?: number;
    aiTokenLimitMonthly?: number;
    image_generation_limit_monthly?: number;
    imageGenerationLimitMonthly?: number;
    workflow_limit?: number;
    workflowLimit?: number;
    workflow_execution_limit_monthly?: number;
    workflowExecutionLimitMonthly?: number;
    member_limit?: number;
    memberLimit?: number;
    storage_limit_mb?: number;
    storageLimitMb?: number;
    analytics_retention_days?: number;
    analyticsRetentionDays?: number;
    has_api_access?: boolean;
    hasApiAccess?: boolean;
    has_custom_providers?: boolean;
    hasCustomProviders?: boolean;
    has_sso?: boolean;
    hasSSO?: boolean;
    has_2fa?: boolean;
    has2FA?: boolean;
    has_approval_workflows?: boolean;
    hasApprovalWorkflows?: boolean;
    has_automation?: boolean;
    hasAutomation?: boolean;
    has_advanced_analytics?: boolean;
    hasAdvancedAnalytics?: boolean;
  };
}

export interface Subscription {
  id: string;
  organisation_id?: string;
  organisationId?: string;
  plan_id?: string;
  planId?: string;
  plan_name?: string;
  plan?: Plan;
  status: string;
  billing_period?: string;
  billingPeriod?: string;
  current_period_start?: string;
  currentPeriodStart?: string;
  current_period_end?: string;
  currentPeriodEnd?: string;
  trial_end?: string | null;
  trialEnd?: string | null;
  cancel_at_period_end?: boolean;
  cancelAtPeriodEnd?: boolean;
  payment_gateway?: string | null;
  paymentGateway?: string | null;
  created_at?: string;
}

export interface UsageMetrics {
  connected_social_accounts?: number;
  connectedSocialAccounts?: number;
  posts_published_this_month?: number;
  postsPublishedThisMonth?: number;
  ai_tokens_consumed_this_month?: number;
  aiTokensUsedThisMonth?: number;
  images_generated_this_month?: number;
  active_workflows?: number;
  activeWorkflows?: number;
  team_members?: number;
  teamMembers?: number;
  limits?: {
    social_account_limit?: number;
    socialAccountLimit?: number;
    monthly_post_limit?: number;
    monthlyPostLimit?: number;
    ai_token_limit_monthly?: number;
    aiTokenLimitMonthly?: number;
    workflow_limit?: number;
    workflowLimit?: number;
    member_limit?: number;
    memberLimit?: number;
  };
}
