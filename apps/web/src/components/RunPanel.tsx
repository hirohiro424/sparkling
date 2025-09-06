"use client";
import { useState } from "react";

export default function RunPanel({ promptId }: { promptId: number }) {
  const [inputText, setInputText] = useState("");
  const [output, setOutput] = useState<string>("");
  const [lastRunId, setLastRunId] = useState<number | null>(null);

  const [score, setScore] = useState<string>("");

  const run = async () => {
    const res = await fetch("http://localhost:8000/runs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt_id: promptId,
        input_text: inputText,
        model: "gpt-5",
      }),
    });
    const data = await res.json();
    setOutput(data.output_text ?? "");
    setLastRunId(data.id ?? null);     // 평가 때 쓸 runId 저장
    setScore("");                      // 이전 점수 초기화
  };

  const evaluate = async () => {
    if (lastRunId == null) return alert("먼저 Run을 실행해줘.");
    const res = await fetch(`http://localhost:8000/evals/${lastRunId}`, { method: "POST" });
    const data = await res.json();
    setScore(JSON.stringify(data, null, 2));
  };

  return (
    <div className="border rounded p-3 space-y-2">
      <h3 className="font-semibold">Test Runner</h3>

      <textarea
        className="w-full border rounded p-2"
        rows={4}
        placeholder="Enter test input..."
        value={inputText}
        onChange={(e) => setInputText(e.target.value)}
      />

      <div className="flex gap-2">
        <button className="px-2 py-1 border rounded" onClick={run}>Run</button>
        <button
          className="px-2 py-1 border rounded disabled:opacity-50"
          onClick={evaluate}
          disabled={lastRunId == null}
          title={lastRunId == null ? "먼저 Run을 실행해" : `Run #${lastRunId} 평가`}
        >
          Evaluate last run
        </button>
      </div>

      {lastRunId != null && (
        <p className="text-sm opacity-70">Last run id: {lastRunId}</p>
      )}

      <div>
        <h4 className="font-medium mt-2 mb-1">Output</h4>
        <pre className="whitespace-pre-wrap border rounded p-2 bg-black/5 dark:bg-white/10">
          {output}
        </pre>
      </div>

      <div>
        <h4 className="font-medium mt-2 mb-1">Evaluation</h4>
        <pre className="whitespace-pre-wrap border rounded p-2 bg-black/5 dark:bg-white/10">
          {score}
        </pre>
      </div>
    </div>
  );
}
