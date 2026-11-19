import { getCreatePermission } from './permissions.js'

export async function getActivityCreatePermissions(request) {
  const [task, note] = await Promise.all([
    getCreatePermission(request, 'DoubleT Task'),
    getCreatePermission(request, 'DoubleT Note'),
  ])
  return { canCreateTask: task.allowed, canCreateNote: note.allowed }
}

export function runCreateAction(allowed, action) {
  if (!allowed || typeof action !== 'function') return false
  action()
  return true
}
