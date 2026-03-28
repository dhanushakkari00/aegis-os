import { render, screen } from "@testing-library/react";

import { IntakeComposer } from "@/components/intake-composer";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() })
}));

describe("IntakeComposer", () => {
  it("renders primary intake controls", () => {
    render(<IntakeComposer />);
    expect(screen.getByLabelText("Primary intake")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /launch analysis/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /auto detect/i })).toBeInTheDocument();
  });
});

