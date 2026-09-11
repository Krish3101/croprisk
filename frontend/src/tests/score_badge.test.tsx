import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ScoreBadge } from "../components/ScoreBadge";

describe("ScoreBadge Component", () => {
  it("renders LOW severity correctly with accessible text label and score", () => {
    render(<ScoreBadge score={17} severity="LOW" />);
    const badge = screen.getByTestId("score-badge");
    expect(badge).toHaveTextContent("LOW RISK");
    expect(badge).toHaveTextContent("(17/100)");
  });

  it("renders MODERATE severity correctly with warning symbol and label", () => {
    render(<ScoreBadge score={57} severity="MODERATE" />);
    const badge = screen.getByTestId("score-badge");
    expect(badge).toHaveTextContent("MODERATE RISK");
    expect(badge).toHaveTextContent("(57/100)");
  });

  it("renders HIGH severity correctly with alert label and score", () => {
    render(<ScoreBadge score={100} severity="HIGH" />);
    const badge = screen.getByTestId("score-badge");
    expect(badge).toHaveTextContent("HIGH RISK");
    expect(badge).toHaveTextContent("(100/100)");
  });
});
