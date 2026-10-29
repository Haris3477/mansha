<!-- Posted by Haris as https://github.com/tashfeenahmed/freellmapi/issues/1757 on 29 Oct 2026. Title on the first line below the comment. -->
Google per-model 503 ("high demand") rules out the whole google platform for the request (#788), so a sibling Gemini is never tried

**Version:** reproduced on 986b2118; the same code is still on main at 36826e7 (`server/src/lib/fallback-loop.ts` `recordRetryableFailure`, `server/src/lib/error-classify.ts` `isProviderLevelError`).

**What happens**
A chain/alias with two Google models (e.g. `gemini-3.6-flash` and `gemini-3.5-flash`). The first routed model returns:

```
Google API error 503: This model is currently experiencing high demand. Spikes in demand are usually temporary...
```

`isProviderLevelError` is true for any status >= 500, so `recordRetryableFailure` adds `google` to `state.skipPlatforms` (#788). The sibling Gemini is skipped for the rest of the request, and the client gets:

```
502 All 1 routed attempt(s) failed with upstream provider errors ...
```

**Why the platform-wide skip is wrong here**
Google's "high demand" 503 is per model, not a provider outage. In our `requests` table it repeatedly hits one Gemini while another serves normally. Example: 21:55:27 UTC `gemini-3.6-flash` 503 (11.5 s), and a client resend 45 s later served by `gemini-3.5-flash` (success, 14.4 s). Over 14–26 Oct we saw many single-model 503s with other Gemini models healthy in the same minute.

**Expected**
On a Google 503 whose body says the model is overloaded / high demand (status `UNAVAILABLE`), skip that model (or that model+key) for the request, not the platform, so the next Gemini in the chain is tried in the same request. A true provider outage (timeouts, connection errors, `fetch failed`) can keep the platform-wide rule.

**Possible fix**
In `recordRetryableFailure`, before `state.skipPlatforms.add(route.platform)`:

```ts
const msg = String(err?.message ?? '').toLowerCase();
const perModelOverload = route.platform === 'google' && err?.status === 503
  && (msg.includes('high demand') || msg.includes('overloaded'));
if (perModelOverload) state.skipModels.add(route.modelDbId);
else if (isProviderLevelError(err)) state.skipPlatforms.add(route.platform);
```

(or a more general "model-scoped 5xx" classifier in `error-classify.ts`). The per-key cooldown below already benches the failed model, so later requests are unaffected either way.

**Workaround we use**
The client resends after ~3 s on a 502 for that chain. The failed model is already benched, so the resend reaches the sibling model.
