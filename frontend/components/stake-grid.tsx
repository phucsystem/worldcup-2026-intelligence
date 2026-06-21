import type { GroupScenario } from "@/lib/api";
import StakeCard from "@/components/stake-card";

export default function StakeGrid({ scenarios }: { scenarios: GroupScenario[] }) {
  if (!scenarios || scenarios.length === 0) return null;
  return (
    <div className="stake-grid">
      {scenarios.map((s) => (
        <StakeCard key={s.group_name} scenario={s} />
      ))}
    </div>
  );
}
