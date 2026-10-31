// Deep links: ?field=<field_id> opens the app on that Live field (ADR 0034).

/** field_id in the page URL, or null. */
export function urlField(search: string): string | null {
  const id = new URLSearchParams(search).get("field");
  return id && id.trim() !== "" ? id : null;
}

/** Shareable link to a Live field, relative to the app's own address (sub-path safe). */
export function fieldLink(fieldId: string): string {
  const u = new URL(window.location.href);
  u.search = "";
  u.searchParams.set("field", fieldId);
  return u.toString();
}

/** Keep the address bar pointing at the selected field so it can be shared. */
export function setUrlField(fieldId: string | null): void {
  const u = new URL(window.location.href);
  if (fieldId) u.searchParams.set("field", fieldId);
  else u.searchParams.delete("field");
  window.history.replaceState(null, "", u);
}
