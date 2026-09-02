export const FRONTEND_VERSION = "1.0.0";
export const MIN_COMPATIBLE_BACKEND_VERSION = "1.0.0";
export const API_VERSION = "v1";
export const RELEASE_CODENAME = "StreamFlow";

export interface SystemVersionInfo {
  backend_version: string;
  frontend_version: string;
  shared_types_version: string;
  api_version: string;
  schema_version: string;
  codename: string;
  environment: string;
  status: string;
}
