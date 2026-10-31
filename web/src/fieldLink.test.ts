import { describe, expect, it } from "vitest";
import { urlField } from "./fieldLink";

describe("urlField", () => {
  it("reads a field id", () => {
    expect(urlField("?field=LWK-2026-1234")).toBe("LWK-2026-1234");
    expect(urlField("?lang=de&field=f2")).toBe("f2");
  });
  it("is null without or with an empty id", () => {
    expect(urlField("")).toBeNull();
    expect(urlField("?field=")).toBeNull();
    expect(urlField("?lang=de")).toBeNull();
  });
});
