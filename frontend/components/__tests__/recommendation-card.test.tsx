import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { RecommendationCard } from "../recommendation-card";

describe("RecommendationCard", () => {
  const mockAction = {
    priority: 1,
    title: "Escalate to emergency care",
    description: "Advise immediate EMS evaluation.",
    category: "medical",
    rationale: "High-risk pattern detected.",
    is_immediate: true
  };

  it("renders the action title", () => {
    render(<RecommendationCard action={mockAction} />);
    expect(screen.getByText("Escalate to emergency care")).toBeInTheDocument();
  });

  it("renders the action description", () => {
    render(<RecommendationCard action={mockAction} />);
    expect(screen.getByText("Advise immediate EMS evaluation.")).toBeInTheDocument();
  });

  it("renders priority label", () => {
    render(<RecommendationCard action={mockAction} />);
    expect(screen.getByText(/Priority 1/i)).toBeInTheDocument();
  });
});
