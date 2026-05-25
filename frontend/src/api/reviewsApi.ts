import type { AnalyzeReviewsRequest, ReviewAnalysisResponse } from "../types/reviews";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const ANALYZE_ENDPOINT = "/api/reviews/parse-prepare-analyze-evaluate";

export async function analyzeProductReviews(
  payload: AnalyzeReviewsRequest
): Promise<ReviewAnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}${ANALYZE_ENDPOINT}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(data?.detail ?? `Request failed with status ${response.status}`);
  }

  return data as ReviewAnalysisResponse;
}
