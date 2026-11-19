export function linkedDocLookupState(resource) {
  if (resource?.loading || (!resource?.data && !resource?.error)) {
    return { status: 'loading', docs: [], message: '' }
  }
  if (resource?.error) {
    const message =
      resource.error?.messages?.join?.('; ') ||
      resource.error?._server_messages?.join?.('; ') ||
      resource.error?.message ||
      'Unable to check linked documents.'
    return { status: 'error', docs: [], message }
  }
  if (resource.data?.complete !== true) {
    return {
      status: 'error',
      docs: [],
      message: 'Not all linked documents could be verified. Please retry.',
    }
  }
  return {
    status: 'success',
    docs: Array.isArray(resource.data.docs) ? resource.data.docs : [],
    message: '',
  }
}
