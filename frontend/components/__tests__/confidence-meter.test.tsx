import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ConfidenceMeter } from "../confidence-meter";

describe("ConfidenceMeter", () => {
  it("renders the confidence percentage", () => {
    render(<ConfidenceMeter confidence={0.89} />);
    expect(screen.getByText("89%")).toBeInTheDocument();
  });

  it("renders zero confidence without crashing", () => {
    render(<ConfidenceMeter confidence={0} />);
    expect(screen.getByText("0%")).toBeInTheDocument();
  });

  it("clamps to 100% for values at 1.0", () => {
    render(<ConfidenceMeter confidence={1.0} />);
    expect(screen.getByText("100%")).toBeInTheDocument();
  });
});
