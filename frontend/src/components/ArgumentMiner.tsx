import { useState } from "react";
import { runArgumentMiner } from "../api";
import { ArgumentMinerResponse } from "../types";

const ArgumentMiner = () => {
  const [input, setInput] = useState("");
  const [mode, setMode] = useState<"case" | "facts" | "hybrid">("facts");
  const [result, setResult] = useState<ArgumentMinerResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      const payload =
        mode === "case"
          ? { mode, case_id: input }
          : mode === "facts"
          ? { mode, facts: input }
          : { mode, case_id: input, facts: input };

      const data = await runArgumentMiner(payload);
      setResult(data);
    } catch (err) {
      console.error(err);
      alert("Argument mining failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: "20px" }}>
      <h2>Argument Miner</h2>

      <select
        value={mode}
        onChange={(e) => setMode(e.target.value as any)}
        style={{ marginBottom: "10px" }}
      >
        <option value="facts">Facts</option>
        <option value="case">Case ID</option>
        <option value="hybrid">Hybrid</option>
      </select>

      <textarea
        rows={6}
        placeholder={
          mode === "case"
            ? "Enter case id..."
            : "Enter case facts..."
        }
        value={input}
        onChange={(e) => setInput(e.target.value)}
        style={{ width: "100%", marginBottom: "10px" }}
      />

      <button onClick={handleAnalyze} disabled={loading}>
        {loading ? "Analyzing..." : "Analyze Arguments"}
      </button>

      {result && (
        <>
          <div style={{ display: "flex", gap: "20px", marginTop: "20px" }}>
            <div style={{ flex: 1 }}>
              <h3>Prosecution Arguments</h3>
              <ul>
                {result.prosecution_arguments.map((arg, i) => (
                  <li key={i}>{arg}</li>
                ))}
              </ul>
            </div>

            <div style={{ flex: 1 }}>
              <h3>Defense Arguments</h3>
              <ul>
                {result.defense_arguments.map((arg, i) => (
                  <li key={i}>{arg}</li>
                ))}
              </ul>
            </div>
          </div>

          <div
            style={{
              marginTop: "20px",
              padding: "15px",
              border: "1px solid green",
              borderRadius: "8px",
            }}
          >
            <h3>Winning Argument (Predicted)</h3>
            <p>{result.winning_argument.reasoning}</p>
            <strong>Confidence: {result.winning_argument.confidence}%</strong>
          </div>
        </>
      )}
    </div>
  );
};

export default ArgumentMiner;
