import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { UrgencyBadge } from "../urgency-badge";

describe("UrgencyBadge", () => {
  it("renders critical urgency", () => {
    render(<UrgencyBadge urgency="critical" />);
    expect(screen.getByText(/critical/i)).toBeInTheDocument();
  });

  it("renders high urgency", () => {
    render(<UrgencyBadge urgency="high" />);
    expect(screen.getByText(/high/i)).toBeInTheDocument();
  });

  it("renders moderate urgency", () => {
    render(<UrgencyBadge urgency="moderate" />);
    expect(screen.getByText(/moderate/i)).toBeInTheDocument();
  });

  it("renders low urgency", () => {
    render(<UrgencyBadge urgency="low" />);
    expect(screen.getByText(/low/i)).toBeInTheDocument();
  });
});
