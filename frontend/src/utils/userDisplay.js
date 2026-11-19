export function normalizeSessionUser(userId) {
  if (typeof userId !== 'string' || !userId || userId === 'Guest') return ''
  return userId
}

export function currentUserDisplayName(userId, getUser, neutralLabel) {
  const currentUserId = normalizeSessionUser(userId)
  if (!currentUserId) return neutralLabel

  let profile = null
  try {
    profile = getUser(currentUserId)
  } catch {
    return currentUserId
  }

  if (!profile || profile.__isTemporaryProfile) return currentUserId
  return profile.full_name?.trim() || currentUserId
}
