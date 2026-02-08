import { useState } from "react";
import { runArgumentMiner } from "../api";
import { ArgumentMinerResponse } from "../types";

const ArgumentMiner = () => {
  const [input, setInput] = useState("");
  const [mode, setMode] = useState<"case" | "facts">("facts");
  const [result, setResult] = useState<ArgumentMinerResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      const payload =
        mode === "case"
          ? { mode, case_id: input }
          : { mode, facts: input };

      const data = await runArgumentMiner(payload);
      setResult(data);
    } catch (err) {
      console.error(err);
      alert("Argument mining failed");
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    // If doc_url is available, open it in a new tab
    if (result?.doc_url) {
      window.open(result.doc_url, '_blank');
    } else {
      // Fallback: copy summary text
      const text = `Prosecution: ${result?.prosecution_arguments.length || 0} | Defense: ${result?.defense_arguments.length || 0} | Confidence: ${result?.winning_argument.confidence}%`;
      navigator.clipboard.writeText(text);
    }
  };

  return (
    <div style={{
      padding: "40px 20px",
      maxWidth: "1200px",
      margin: "0 auto",
      backgroundColor: "#f5f5f5",
      minHeight: "100vh"
    }}>
      {/* Search Section */}
      <div style={{
        backgroundColor: "#ffffff",
        borderRadius: "12px",
        padding: "30px",
        marginBottom: "30px",
        boxShadow: "0 2px 8px rgba(0,0,0,0.1)"
      }}>
        <div style={{ marginBottom: "20px" }}>
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value as any)}
            style={{
              padding: "10px 15px",
              fontSize: "14px",
              border: "1px solid #ddd",
              borderRadius: "6px",
              backgroundColor: "#fff",
              cursor: "pointer"
            }}
          >
            <option value="facts">Facts Mode</option>
            <option value="case">Case ID Mode</option>
          </select>
        </div>

        <div style={{ display: "flex", gap: "15px", alignItems: "flex-start" }}>
          <div style={{ position: "relative", flex: 1 }}>
            <span style={{
              position: "absolute",
              left: "15px",
              top: "15px",
              fontSize: "20px",
              color: "#999"
            }}>🔍</span>
            <textarea
              rows={3}
              placeholder={
                mode === "case"
                  ? "Enter case ID..."
                  : "Enter legal scenario, case facts, or statute..."
              }
              value={input}
              onChange={(e) => setInput(e.target.value)}
              style={{
                width: "100%",
                padding: "15px 15px 15px 45px",
                fontSize: "15px",
                border: "1px solid #ddd",
                borderRadius: "8px",
                resize: "vertical",
                fontFamily: "inherit"
              }}
            />
          </div>
          <button
            onClick={handleAnalyze}
            disabled={loading}
            style={{
              padding: "15px 30px",
              fontSize: "15px",
              fontWeight: "600",
              color: "#fff",
              backgroundColor: loading ? "#999" : "#1e5ba8",
              border: "none",
              borderRadius: "8px",
              cursor: loading ? "not-allowed" : "pointer",
              whiteSpace: "nowrap",
              height: "fit-content"
            }}
          >
            {loading ? "Analyzing..." : "Search"}
          </button>
        </div>
      </div>

      {result && (
        <>
          {/* Two-Column Arguments Layout */}
          <div style={{
            display: "grid",
            gridTemplateColumns: "1fr 1px 1fr",
            gap: "0",
            backgroundColor: "#ffffff",
            borderRadius: "12px",
            padding: "30px",
            marginBottom: "20px",
            boxShadow: "0 2px 8px rgba(0,0,0,0.1)"
          }}>
            {/* Prosecution Arguments */}
            <div>
              <h3 style={{
                fontSize: "20px",
                fontWeight: "700",
                color: "#1a1a1a",
                marginBottom: "20px",
                marginTop: 0
              }}>Prosecution Arguments</h3>
              <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                {result.prosecution_arguments.map((arg, i) => (
                  <li key={i} style={{
                    display: "flex",
                    gap: "10px",
                    marginBottom: "15px",
                    fontSize: "15px",
                    lineHeight: "1.6",
                    color: "#333"
                  }}>
                    <span style={{ color: "#1e5ba8", fontWeight: "bold", flexShrink: 0 }}>›</span>
                    <span>{arg}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Divider */}
            <div style={{ backgroundColor: "#e0e0e0", width: "1px" }} />

            {/* Defense Arguments */}
            <div style={{ paddingLeft: "30px" }}>
              <h3 style={{
                fontSize: "20px",
                fontWeight: "700",
                color: "#1a1a1a",
                marginBottom: "20px",
                marginTop: 0
              }}>Defense Arguments</h3>
              <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                {result.defense_arguments.map((arg, i) => (
                  <li key={i} style={{
                    display: "flex",
                    gap: "10px",
                    marginBottom: "15px",
                    fontSize: "15px",
                    lineHeight: "1.6",
                    color: "#333"
                  }}>
                    <span style={{ color: "#1e5ba8", fontWeight: "bold", flexShrink: 0 }}>›</span>
                    <span>{arg}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Winning Argument Card */}
          <div style={{
            backgroundColor: "#e8f5e9",
            border: "2px solid #4caf50",
            borderRadius: "12px",
            padding: "25px",
            marginBottom: "20px",
            boxShadow: "0 2px 8px rgba(76,175,80,0.2)"
          }}>
            <div style={{ display: "flex", alignItems: "flex-start", gap: "15px" }}>
              <span style={{
                fontSize: "24px",
                color: "#4caf50",
                flexShrink: 0
              }}>✓</span>
              <div style={{ flex: 1 }}>
                <h3 style={{
                  fontSize: "18px",
                  fontWeight: "700",
                  color: "#2e7d32",
                  marginTop: 0,
                  marginBottom: "15px"
                }}>Winning Argument (Predicted)</h3>
                <p style={{
                  fontSize: "15px",
                  lineHeight: "1.6",
                  color: "#1b5e20",
                  marginBottom: "15px"
                }}>{result.winning_argument.reasoning}</p>

                {/* Confidence Progress Bar */}
                <div>
                  <div style={{
                    height: "8px",
                    backgroundColor: "#c8e6c9",
                    borderRadius: "4px",
                    overflow: "hidden",
                    marginBottom: "8px"
                  }}>
                    <div style={{
                      height: "100%",
                      width: `${result.winning_argument.confidence}%`,
                      backgroundColor: "#4caf50",
                      transition: "width 0.3s ease"
                    }} />
                  </div>
                  <strong style={{ fontSize: "14px", color: "#2e7d32" }}>
                    Confidence: {result.winning_argument.confidence}%
                  </strong>
                </div>
              </div>
            </div>
          </div>

          {/* Source Citation */}
          <div style={{
            backgroundColor: "#ffffff",
            borderRadius: "12px",
            padding: "20px 25px",
            boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center"
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <span style={{ fontSize: "20px", color: "#666" }}>📄</span>
              <div>
                <div style={{ fontSize: "14px", fontWeight: "600", color: "#666", marginBottom: "4px" }}>
                  Source Citation:
                </div>
                <div style={{ fontSize: "14px", color: "#333" }}>
                  {mode === "case" ? `Case ID: ${input}` : "Analysis based on provided facts"}
                </div>
              </div>
            </div>
            <button
              onClick={handleCopy}
              style={{
                padding: "8px 20px",
                fontSize: "14px",
                fontWeight: "500",
                color: "#1e5ba8",
                backgroundColor: "#fff",
                border: "1px solid #1e5ba8",
                borderRadius: "6px",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "8px"
              }}
            >
              <span>{result.doc_url ? "🔗" : "📋"}</span> {result.doc_url ? "View Document" : "Copy"}
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default ArgumentMiner;

