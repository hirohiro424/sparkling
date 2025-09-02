"use client";
import { useEffect, useState } from "react";
import Editor from "@monaco-editor/react";
import axios from "axios";

/** ← 여기 컴포넌트 그대로 붙여 넣기 */
function EventTimeline({ promptId }: { promptId: number }) {
  const [events, setEvents] = useState<any[]>([]);
  const load = async () => {
    const res = await axios.get(`http://localhost:8000/prompts/${promptId}/events`);
    setEvents(res.data);
  };
  useEffect(() => { load(); }, [promptId]);

  const rollback = async (id: number) => {
    await axios.post(`http://localhost:8000/prompts/${promptId}/rollback`, null, { params: { target_event_id: id } });
    await load();
    alert(`rolled back to event ${id}`);
  };

  return (
    <div className="mt-4 space-y-2">
      <h3 className="font-semibold">Timeline</h3>
      <ul className="text-sm space-y-1">
        {events.map(e => (
          <li key={e.id} className="flex items-center gap-2">
            <span className="opacity-70">{e.id}</span>
            <span>{e.kind}</span>
            <span className="opacity-70">{new Date(e.created_at).toLocaleString()}</span>
            <button className="px-2 py-0.5 border rounded" onClick={() => rollback(e.id)}>Rollback</button>
          </li>
        ))}
      </ul>
    </div>
  );
}

/** 기존 에디터 컴포넌트 */
export default function PromptEditor({ promptId }: { promptId: number }) {
  const [value, setValue] = useState<string>("");

  useEffect(() => {
    axios.get(`http://localhost:8000/prompts/${promptId}`)
      .then(res => setValue(res.data.text ?? ""))
      .catch(() => setValue(""));
  }, [promptId]);

  const save = async () => {
    await axios.post(`http://localhost:8000/prompts/${promptId}/events`, {
      kind: "SET_FULL_TEXT",
      text: value,
      note: "manual save",
    });
    alert("saved");
  };

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-lg font-semibold">Prompt #{promptId}</h2>
        <button
          onClick={save}
          className="px-3 py-1.5 rounded bg-black text-white dark:bg-white dark:text-black"
        >
          Save
        </button>
      </div>

      <div className="border rounded overflow-hidden h-[60vh]">
        <Editor
          height="100%"
          defaultLanguage="markdown"
          value={value}
          onChange={(v) => setValue(v ?? "")}
          options={{ wordWrap: "on", minimap: { enabled: false } }}
        />
      </div>

      {/* ← 에디터 아래에 타임라인 배치 */}
      <EventTimeline promptId={promptId} />
    </div>
  );
}
