export type ProductContext = {
  store?: string;
  product_url?: string;
  product_id?: string;
  product_name?: string;
  seller?: string;
  source_url?: string;
};

export type UsefulnessFeatures = {
  llm_helpfulness?: number;
  specificity?: number;
  usage_experience?: number;
  pros_cons_balance?: number;
  decision_support?: number;
  spam_risk?: number;
  [key: string]: number | undefined;
};

export type Usefulness = {
  score?: number;
  category?: string;
  is_helpful?: boolean;
  features?: UsefulnessFeatures;
};

export type Classification = {
  topic_category?: string;
  sentiment?: string;
};

export type LlmAnalysis = {
  helpfulness_score?: number;
  specificity_score?: number;
  usage_experience_score?: number;
  pros_cons_balance_score?: number;
  decision_support_score?: number;
  fake_signal_score?: number;
  category?: string;
  reasoning?: string;
  summary?: string;
  [key: string]: unknown;
};

export type ReviewItem = {
  review_id?: string;
  author?: string | null;
  date?: string | null;
  created_at?: string | null;
  rating?: number | null;
  text?: string | null;
  pros?: string | null;
  cons?: string | null;
  review_text_for_llm?: string | null;
  is_verified_buyer?: boolean;
  word_count?: number | null;
  is_low_information?: boolean;
  analysis_source?: string;
  llm_analysis?: LlmAnalysis;
  usefulness?: Usefulness;
  classification?: Classification;
  summary?: string | null;
  explanation?: string | null;
  helpfulness_score?: number;
  final_helpfulness_score?: number;
  helpfulness_category?: string;
  category?: string;
  [key: string]: unknown;
};

export type ReviewAnalysisResponse = {
  store?: string;
  url?: string;
  product_id?: number | string | null;
  product?: ProductContext;
  raw_reviews_count?: number;
  prepared_reviews_count?: number;
  analyzed_reviews_count?: number;
  evaluated_reviews_count?: number;
  saved_reviews_count?: number;
  saved_analyses_count?: number;
  reviews?: ReviewItem[];
  [key: string]: unknown;
};

export type AnalyzeReviewsRequest = {
  url: string;
  max_pages: number;
};

export type FilterMode = "all" | "high" | "medium" | "low";
export type SortMode = "score_desc" | "score_asc" | "rating_desc" | "rating_asc" | "original";
