const normalizeBaseUrl = (url: string) => url.replace(/\/$/, "");

const getApiBaseUrl = () => {
    const envUrl = import.meta.env.VITE_API_BASE_URL;
    if (envUrl && typeof envUrl === "string") {
        return normalizeBaseUrl(envUrl);
    }
    return "/api/v1";
};

export const API_BASE_URL = getApiBaseUrl();
