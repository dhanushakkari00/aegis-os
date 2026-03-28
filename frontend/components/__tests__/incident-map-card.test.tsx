import { render, screen } from "@testing-library/react";

import { IncidentMapCard } from "@/components/incident-map-card";

describe("IncidentMapCard", () => {
  it("renders a real map preview when coordinates and a map URL are available", () => {
    render(
      <IncidentMapCard
        mapPreviewUrl="/api/v1/dashboard/incident-map"
        pulses={[
          {
            label: "Sector 9",
            severity: "critical",
            note: "Flooding with trapped civilians",
            lat: 12.971599,
            lng: 77.594566
          }
        ]}
      />
    );

    expect(screen.getByAltText("Incident overview map")).toBeInTheDocument();
  });

  it("falls back to the pulse grid when coordinates are not available", () => {
    render(
      <IncidentMapCard
        mapPreviewUrl="/api/v1/dashboard/incident-map"
        pulses={[
          {
            label: "Unknown location",
            severity: "moderate",
            note: "Waiting for precise location"
          }
        ]}
      />
    );

    expect(screen.queryByAltText("Incident overview map")).not.toBeInTheDocument();
    expect(screen.getByText("Unknown location")).toBeInTheDocument();
  });
});
