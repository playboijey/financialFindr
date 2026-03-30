const BASE = "https://financialmodelingprep.com/api/v3";

export default async function handler(req, res) {
  // CORS headers
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") {
    return res.status(200).end();
  }

  const { ticker, type } = req.query;

  if (!ticker) {
    return res.status(400).json({ error: "Missing ticker parameter" });
  }

  const API_KEY = process.env.FMP_API_KEY;

  if (!API_KEY) {
    return res.status(500).json({ error: "API key not configured" });
  }

  const t = ticker.trim().toUpperCase();

  try {
    if (type === "all") {
      const [income, balance, cashflow, profile] = await Promise.all([
        fetch(`${BASE}/income-statement/${t}?limit=1&apikey=${API_KEY}`).then(r => r.json()),
        fetch(`${BASE}/balance-sheet-statement/${t}?limit=1&apikey=${API_KEY}`).then(r => r.json()),
        fetch(`${BASE}/cash-flow-statement/${t}?limit=1&apikey=${API_KEY}`).then(r => r.json()),
        fetch(`${BASE}/profile/${t}?apikey=${API_KEY}`).then(r => r.json()),
      ]);

      if (!Array.isArray(income) || income.length === 0) {
        return res.status(404).json({ error: "Ticker not found or no data available" });
      }

      return res.status(200).json({
        income: income[0],
        balance: balance[0],
        cashflow: cashflow[0],
        profile: profile[0] || null,
      });
    }

    return res.status(400).json({ error: "Invalid type parameter" });

  } catch (err) {
    console.error("FMP fetch error:", err);
    return res.status(502).json({ error: "Failed to fetch financial data" });
  }
}
