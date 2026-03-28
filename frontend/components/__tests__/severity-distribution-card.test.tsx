import { render, screen } from "@testing-library/react";

import { SeverityDistributionCard } from "@/components/severity-distribution-card";

describe("SeverityDistributionCard", () => {
  it("renders heading text", () => {
    render(
      <SeverityDistributionCard
        buckets={[
          { level: "low", count: 1 },
          { level: "moderate", count: 2 },
          { level: "high", count: 3 },
          { level: "critical", count: 4 }
        ]}
      />
    );
    expect(screen.getByText(/severity distribution/i)).toBeInTheDocument();
  });
});

