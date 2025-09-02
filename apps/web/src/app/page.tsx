"use client";
import PromptEditor from "@/components/PromptEditor";
import CriteriaPanel from "@/components/CriteriaPanel";
import RunPanel from "@/components/RunPanel";

export default function Home() {
  return (
    <main className="p-8 grid grid-cols-1 md:grid-cols-12 gap-6">
      <div className="md:col-span-8 col-span-12">
        <PromptEditor promptId={1} />
      </div>

      <div className="md:col-span-4 col-span-12 space-y-4">
        <CriteriaPanel promptId={1} />
        <RunPanel promptId={1} />
      </div>
    </main>
  );
}
