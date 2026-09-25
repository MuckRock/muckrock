/**
 * Search the email-autocomplete endpoint (communication.views.EmailAutocomplete).
 *
 * The endpoint speaks Select2: {results: [{id, text, selected_text}]}, with
 * text being EmailAddress.__str__ -- either the bare address or
 * `"Name" <address>`.  Only good addresses are returned.
 */

export interface EmailOption {
  id: number;
  email: string;
  name: string;
}

interface Select2Result {
  id: number | string;
  text: string;
  create_id?: boolean;
}

export function parseLabel(label: string): { email: string; name: string } {
  const match = label.match(/^"(.*)" <([^<>]+)>$/);
  if (match) {
    return { email: match[2], name: match[1] };
  }
  return { email: label, name: "" };
}

export async function searchEmails(
  url: string,
  query: string,
  signal?: AbortSignal,
): Promise<EmailOption[]> {
  const response = await fetch(`${url}?${new URLSearchParams({ q: query })}`, {
    signal,
    credentials: "same-origin",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw new Error(`Email search failed: ${response.status}`);
  }
  const data = await response.json();
  return (data.results ?? [])
    // Staff get a "Create" row; the repair form resolves a typed address on
    // submit, so creating it ahead of time is never needed
    .filter((result: Select2Result) => !result.create_id)
    .map((result: Select2Result) => ({
      id: Number(result.id),
      ...parseLabel(result.text),
    }));
}
