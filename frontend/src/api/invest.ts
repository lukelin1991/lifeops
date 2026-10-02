import { api, type Envelope } from './client'
import { crudApi } from './crud'
import type { Holding, Portfolio, WatchlistItem } from './types'

export const investApi = {
  holdings: crudApi<Holding>('/invest/holdings'),
  watchlist: crudApi<WatchlistItem>('/invest/watchlist'),

  portfolio: () => api.get<Portfolio>('/invest/portfolio'),
  watchlistWithPrices: () =>
    api
      .get<Envelope<WatchlistItem[]>>('/invest/watchlist', {
        with_prices: true,
      })
      .then((r) => r.data),
}
