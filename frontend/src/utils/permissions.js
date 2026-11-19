export async function getCreatePermission(request, doctype) {
  try {
    const result = await request('frappe.client.has_permission', {
      doctype,
      docname: '',
      perm_type: 'create',
    })
    return { allowed: Boolean(result?.has_permission), error: null }
  } catch (error) {
    return { allowed: false, error }
  }
}

export async function getDocumentMutationPermissions(request, doctype, docname) {
  try {
    const result = await request('frappe.client.get_doc_permissions', {
      doctype,
      docname,
    })
    return {
      write: Boolean(result?.permissions?.write),
      delete: Boolean(result?.permissions?.delete),
      error: null,
    }
  } catch (error) {
    return { write: false, delete: false, error }
  }
}
