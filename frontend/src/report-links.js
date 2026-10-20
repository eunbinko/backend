export function hasOfficialPdf(report) {
  return typeof report?.pdf_url === 'string' && report.pdf_url.startsWith('https://')
}

export function getOfficialReportUrl(report) {
  return report?.landing_page_url || report?.source_url || null
}
