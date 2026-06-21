import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { UserPreferences, Restaurant } from '../types'

/**
 * A stable signature of every preference field that actually changes the
 * restaurant results. When this string is unchanged, we keep the cached
 * results instead of re-running the (slow) Google Places + Claude pipeline.
 * Location is rounded to ~11 m so GPS jitter doesn't trigger needless refetches.
 */
function buildSignature(p: UserPreferences): string {
  if (p.latitude === undefined || p.longitude === undefined) return ''
  return JSON.stringify([
    p.latitude.toFixed(4),
    p.longitude.toFixed(4),
    p.dietary_styles,
    p.allergens,
    p.liked_ingredients,
    p.disliked_ingredients,
    p.preferred_cuisines,
    p.disliked_cuisines,
    p.requires_open_now,
  ])
}

export interface RestaurantSearchState {
  restaurants: Restaurant[]
  loading: boolean
  error: string | null
}

/**
 * Lives at the App level so it runs no matter which tab is open. Whenever the
 * location or a result-affecting preference changes, it prefetches the matched
 * restaurants in the background (debounced) — so opening Discover is instant.
 */
export function useRestaurantSearch(preferences: UserPreferences): RestaurantSearchState {
  const [restaurants, setRestaurants] = useState<Restaurant[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const lastSig = useRef('')
  const reqId = useRef(0)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  const signature = buildSignature(preferences)

  useEffect(() => {
    if (!signature) return // no location yet
    if (signature === lastSig.current) return // cached — nothing meaningful changed

    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      const myReq = ++reqId.current
      setLoading(true)
      setError(null)
      api
        .searchRestaurantsGoogle({
          preferences,
          latitude: preferences.latitude!,
          longitude: preferences.longitude!,
          radius_meters: 2000,
          limit: 30,
        })
        .then((res) => {
          if (myReq !== reqId.current) return // a newer request superseded this one
          setRestaurants(res.restaurants)
          lastSig.current = signature
        })
        .catch(() => {
          if (myReq !== reqId.current) return
          setError('Could not load restaurants from Google Places.')
        })
        .finally(() => {
          if (myReq === reqId.current) setLoading(false)
        })
    }, 700)

    return () => clearTimeout(debounceRef.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [signature])

  return { restaurants, loading, error }
}
