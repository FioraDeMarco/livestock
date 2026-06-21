import Anthropic from "@anthropic-ai/sdk";

const ML_BACKEND_URL = process.env.ML_BACKEND_URL || "http://localhost:8000";

type Prediction = {
  ticker: string;
  horizon_days: number;
  probability_up: number;
  top_features: { feature: string; shap_value: number }[];
  model_accuracy: number;
  majority_baseline: number;
  accuracy_ci_95: [number, number];
  mcnemar_p: number;
  is_significant: boolean;
};

export async function GET(
  request: Request,
  { params }: { params: Promise<{ ticker: string }> }
) {
  const { ticker } = await params;
  const upperTicker = ticker.toUpperCase();

  let prediction: Prediction;
  try {
    const res = await fetch(`${ML_BACKEND_URL}/predict/${upperTicker}`);
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      return Response.json(
        {
          ticker: upperTicker,
          summary:
            body.detail ?? "AI outlook is not available for this company.",
          topFeatures: [],
        },
        { status: res.status }
      );
    }
    prediction = await res.json();
  } catch {
    return Response.json(
      {
        ticker: upperTicker,
        summary:
          "AI outlook is temporarily unavailable (ML backend not reachable).",
        topFeatures: [],
      },
      { status: 502 }
    );
  }

  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return Response.json({
      ticker: upperTicker,
      probabilityUp: prediction.probability_up,
      modelAccuracy: prediction.model_accuracy,
      majorityBaseline: prediction.majority_baseline,
      accuracyCi95: prediction.accuracy_ci_95,
      isSignificant: prediction.is_significant,
      topFeatures: prediction.top_features,
      summary: "AI synthesis is not configured (missing ANTHROPIC_API_KEY).",
    });
  }

  const client = new Anthropic({ apiKey });

  const systemPrompt = `You explain a stock-direction prediction model's output in plain English for an exploratory research tool. Never give investment advice or imply the prediction is reliable enough to act on.

The model's own backtested accuracy is ${(prediction.model_accuracy * 100).toFixed(1)}%, against a majority-class baseline of ${(prediction.majority_baseline * 100).toFixed(1)}%. This has ${prediction.is_significant ? "" : "NOT "}been confirmed statistically significant (McNemar's test, p=${prediction.mcnemar_p.toFixed(3)}). ${prediction.is_significant ? "" : "Since it is not significant, treat the probability estimate as unproven -- state plainly that no validated edge over the baseline has been found, not just that the edge is small."} State this context plainly, never implying more confidence than the numbers support.

Write 2-3 sentences explaining what's driving the model's current output, based on the SHAP feature contributions given. Use plain language, not technical jargon (e.g. say "the stock's momentum relative to its 50-day average" instead of "close_to_sma50").`;

  const userPrompt = `Ticker: ${upperTicker}
Horizon: ${prediction.horizon_days} days
Model's probability estimate that price goes up: ${(prediction.probability_up * 100).toFixed(1)}%

Top contributing features (signed SHAP values):
${prediction.top_features.map((f) => `- ${f.feature}: ${f.shap_value}`).join("\n")}`;

  try {
    const message = await client.messages.create({
      model: "claude-opus-4-8",
      max_tokens: 512,
      system: systemPrompt,
      messages: [{ role: "user", content: userPrompt }],
    });

    const textBlock = message.content.find((block) => block.type === "text");

    return Response.json({
      ticker: upperTicker,
      probabilityUp: prediction.probability_up,
      modelAccuracy: prediction.model_accuracy,
      majorityBaseline: prediction.majority_baseline,
      accuracyCi95: prediction.accuracy_ci_95,
      isSignificant: prediction.is_significant,
      topFeatures: prediction.top_features,
      summary:
        textBlock?.type === "text" ? textBlock.text : "AI synthesis unavailable.",
    });
  } catch (error) {
    const message =
      error instanceof Anthropic.APIError ? error.message : "Unknown error";
    return Response.json({
      ticker: upperTicker,
      probabilityUp: prediction.probability_up,
      modelAccuracy: prediction.model_accuracy,
      majorityBaseline: prediction.majority_baseline,
      accuracyCi95: prediction.accuracy_ci_95,
      isSignificant: prediction.is_significant,
      topFeatures: prediction.top_features,
      summary: `AI synthesis failed: ${message}`,
    });
  }
}
