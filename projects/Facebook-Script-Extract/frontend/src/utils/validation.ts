const FACEBOOK_PATTERNS = [
  /^https?:\/\/(?:www\.)?facebook\.com\/watch\?v=[\w-]+/,
  /^https?:\/\/(?:www\.)?facebook\.com\/share\/v\/[\w-]+\/?/,
  /^https?:\/\/(?:www\.)?facebook\.com\/share\/r\/[\w-]+\/?/,
  /^https?:\/\/fb\.watch\/[\w-]+/,
  /^https?:\/\/(?:www\.)?facebook\.com\/[^/]+\/videos\/[\w-]+/,
  /^https?:\/\/(?:www\.)?facebook\.com\/groups\/[^/]+\/posts\/[\w-]+/,
  /^https?:\/\/(?:www\.)?facebook\.com\/ads\/library\/\?id=[\d]+/,
]

const YOUTUBE_PATTERNS = [
  /^https?:\/\/(?:www\.)?youtube\.com\/watch\?v=[\w-]+/,
  /^https?:\/\/(?:www\.)?youtube\.com\/shorts\/[\w-]+/,
  /^https?:\/\/youtu\.be\/[\w-]+/,
  /^https?:\/\/(?:www\.)?youtube\.com\/embed\/[\w-]+/,
  /^https?:\/\/(?:www\.)?youtube\.com\/v\/[\w-]+/,
]

const VIDEO_PATTERNS = [...FACEBOOK_PATTERNS, ...YOUTUBE_PATTERNS]

export function isValidVideoUrl(url: string): boolean {
  if (!url || !url.startsWith('http')) return false
  return VIDEO_PATTERNS.some((pattern) => pattern.test(url))
}
