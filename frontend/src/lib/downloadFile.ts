/**
 * Hand the reader a generated file.
 *
 * Object URLs are not available in every environment (jsdom under test, and
 * some embedded webviews); callers get `false` so they can say the export
 * failed rather than appearing to do nothing.
 *
 * The object URL is revoked on the next frame rather than immediately —
 * Safari has not started reading the blob when the click returns, and
 * revoking too early gives the user an empty file.
 */
export function downloadTextFile(
  fileName: string,
  contents: string,
  mimeType = 'text/csv;charset=utf-8',
): boolean {
  if (typeof URL?.createObjectURL !== 'function') {
    return false;
  }

  const url = URL.createObjectURL(new Blob([contents], { type: mimeType }));
  const link = document.createElement('a');
  link.href = url;
  link.download = fileName;
  link.rel = 'noopener';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  setTimeout(() => URL.revokeObjectURL(url), 0);

  return true;
}
