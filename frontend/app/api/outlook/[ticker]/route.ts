export async function GET(
  request: Request,
  { params }: { params: Promise<{ ticker: string }> }
) {
  const { ticker } = await params;

  return Response.json({
    ticker: ticker.toUpperCase(),
    summary:
      "AI outlook synthesis is not yet available. This will summarize the top SHAP features from the XGBoost model once the ML backend is built.",
    topFeatures: [],
  });
}
