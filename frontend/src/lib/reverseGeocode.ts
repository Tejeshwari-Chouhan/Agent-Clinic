/** BigDataCloud client reverse-geocode (browser CORS–friendly, no API key). */
export type ReverseGeocodePayload = {
  locality?: string;
  city?: string;
  village?: string;
  principalSubdivision?: string;
  countryName?: string;
};

export function patientLocationLineFromGeo(data: ReverseGeocodePayload): string {
  const city = data.locality || data.city || data.village || '';
  const region = data.principalSubdivision || '';
  const country = data.countryName || '';
  return [city, region, country].filter(Boolean).join(', ');
}

export async function reverseGeocodeClient(latitude: number, longitude: number): Promise<string> {
  const url = new URL('https://api.bigdatacloud.net/data/reverse-geocode-client');
  url.searchParams.set('latitude', String(latitude));
  url.searchParams.set('longitude', String(longitude));
  url.searchParams.set('localityLanguage', 'en');

  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`Reverse geocode failed (${res.status})`);
  const data = (await res.json()) as ReverseGeocodePayload;
  const line = patientLocationLineFromGeo(data);
  if (!line) throw new Error('Could not resolve city or region from coordinates');
  return line;
}
