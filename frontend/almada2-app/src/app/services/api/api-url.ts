export function construirApiUrl(): string {
  const host =
    typeof window !== 'undefined' && window.location.hostname
      ? window.location.hostname
      : '127.0.0.1';

  return `http://${host}:5000/api`;
}
