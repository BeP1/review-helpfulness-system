import type { ReviewItem } from "../types/reviews";

export function getReviewScore(review: ReviewItem): number {
  const usefulnessScore = review.usefulness?.score;
  if (typeof usefulnessScore === "number") return usefulnessScore;

  const direct = review.final_helpfulness_score ?? review.helpfulness_score;
  if (typeof direct === "number") return direct;

  const fromLlm = review.llm_analysis?.helpfulness_score;
  if (typeof fromLlm === "number") return fromLlm;

  return 0;
}

export function getScoreTier(score: number): "high" | "medium" | "low" {
  if (score >= 60) return "high";
  if (score >= 30) return "medium";
  return "low";
}

export const ROZETKA_URL_PATTERN =
  /^https?:\/\/(www\.)?rozetka\.com\.ua\/(ua\/)?[\w%-]+\/p\d+\/(comments\/?)?$/;

export function isValidRozetkaUrl(url: string): boolean {
  return ROZETKA_URL_PATTERN.test(url.trim());
}
