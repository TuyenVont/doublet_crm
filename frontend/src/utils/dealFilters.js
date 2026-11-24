export function buildDealListFilters(options = {}) {
  const filters = {}
  if (options.stage) filters.stage = options.stage
  if (options.dealOwner) filters.deal_owner = options.dealOwner
  if (options.creationStart && options.creationEnd) {
    filters.creation = [
      'between',
      [`${options.creationStart} 00:00:00`, `${options.creationEnd} 23:59:59.999999`],
    ]
  }
  return filters
}
