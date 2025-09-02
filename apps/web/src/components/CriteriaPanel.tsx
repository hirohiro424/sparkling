"use client";
import { useEffect, useState } from "react";

type Criterion = { 
  id?: number; 
  key: string; 
  desc: string; 
  type: "boolean" | "score"; 
  weight: number 
};

export default function CriteriaPanel({ promptId }: { promptId: number }) {
  const [items, setItems] = useState<Criterion[]>([]);

  const load = async () => {
    const res = await fetch(`http://localhost:8000/criteria/${promptId}`);
    setItems(await res.json());
  };

  const save = async () => {
    await fetch(`http://localhost:8000/criteria/${promptId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(items.map(({ id, ...rest }) => rest)),
    });
    await load();
  };

  useEffect(() => { load(); }, [promptId]);

  return (
    <div className="border rounded p-3 space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">Success Criteria</h3>
        <button className="px-2 py-1 border rounded" onClick={save}>
          Save
        </button>
      </div>

      {items.map((c, idx) => (
        <div 
          key={`${c.id ?? "new"}-${idx}`} 
          className="grid grid-cols-12 gap-2 items-center"
        >
          <input
            className="col-span-2 border rounded px-2 py-1"
            value={c.key}
            onChange={(e) => {
              const v = [...items];
              v[idx] = { ...c, key: e.target.value };
              setItems(v);
            }}
          />
          <input
            className="col-span-6 border rounded px-2 py-1"
            value={c.desc}
            onChange={(e) => {
              const v = [...items];
              v[idx] = { ...c, desc: e.target.value };
              setItems(v);
            }}
          />
          <select
            className="col-span-2 border rounded px-2 py-1"
            value={c.type}
            onChange={(e) => {
              const v = [...items];
              v[idx] = { ...c, type: e.target.value as any };
              setItems(v);
            }}
          >
            <option value="boolean">boolean</option>
            <option value="score">score</option>
          </select>
          <input
            className="col-span-1 border rounded px-2 py-1"
            type="number"
            step="0.1"
            value={c.weight}
            onChange={(e) => {
              const v = [...items];
              v[idx] = { ...c, weight: parseFloat(e.target.value) };
              setItems(v);
            }}
          />
          <button
            className="col-span-1 text-red-500 border rounded px-2 py-1"
            onClick={() => {
              const v = items.filter((_, i) => i !== idx);
              setItems(v);
            }}
          >
            ✕
          </button>
        </div>
      ))}

      <button
        className="px-2 py-1 border rounded"
        onClick={() =>
          setItems([
            ...items,
            { key: `c${items.length + 1}`, desc: "", type: "boolean", weight: 1 },
          ])
        }
      >
        + Add criterion
      </button>
    </div>
  );
}
