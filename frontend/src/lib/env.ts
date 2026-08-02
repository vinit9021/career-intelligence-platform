const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

if (!apiBaseUrl) {
  throw new Error(
    "NEXT_PUBLIC_API_BASE_URL is required. Create frontend/.env.local from frontend/.env.example.",
  );
}

export const env = Object.freeze({
  apiBaseUrl,
});
