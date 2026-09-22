/**
 * Hand the reader a generated file.
 *
 * Object URLs are not available in every environment (jsdom under test, and
 * some embedded webviews); callers get `false` so they can say the export
 * failed rather than appearing to do nothing.
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
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);

  return true;
}
