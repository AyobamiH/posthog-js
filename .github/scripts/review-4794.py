from pathlib import Path


def replace(path, before, after, count=1):
    p = Path(path)
    text = p.read_text()
    actual = text.count(before)
    if actual != count:
        raise RuntimeError(f'{path}: expected {count} occurrences, got {actual}: {before[:100]}')
    p.write_text(text.replace(before, after))


p = 'packages/browser/src/posthog-surveys.ts'
replace(p, "type SurveysClientState = Pick<Client, 'projectToken' | 'kv'>", """type SurveysClientState = Pick<Client, 'projectToken' | 'kv'>

type ActiveMatchingSurveySubscription = {
    callback: SurveyCallback
    active: boolean
    revision: number
    lastResult?: string
}""")
replace(p, '    private _activeMatchingSurveyCallbacks: SurveyCallback[] = []', '''    private _activeMatchingSurveyCallbacks: ActiveMatchingSurveySubscription[] = []
    private _activeMatchingSurveyConditionsUnsubscribe?: () => void''')
replace(p, '        this._activeMatchingSurveyCallbacks = []', '''        this._activeMatchingSurveyCallbacks.forEach((subscription) => { subscription.active = false })
        this._activeMatchingSurveyCallbacks = []
        this._activeMatchingSurveyConditionsUnsubscribe?.()
        this._activeMatchingSurveyConditionsUnsubscribe = undefined''')
replace(p, '''        // Establish the subscription's initial value before existing load callbacks can capture
        // events and cause activation transitions.
        this._notifyActiveMatchingSurveyCallbacks()''', '''        // Establish the subscription's initial value before existing load callbacks can capture
        // events and cause activation transitions.
        this._startActiveMatchingSurveyConditions()
        this._notifyActiveMatchingSurveyCallbacks()''')
replace(p, '''        logger.error(message, error)
        this._notifySurveyCallbacks({ isLoaded: false, error: message })''', '''        logger.error(message, error)
        this._notifyActiveMatchingSurveyCallbacks({ isLoaded: false, error: message })
        this._notifySurveyCallbacks({ isLoaded: false, error: message })''')
replace(p, '''            // Failure behaves like a response without a surveys key: not loaded.
            return logger.warn('Remote config unavailable. Not loading surveys.')''', '''            this._notifyActiveMatchingSurveyCallbacks({
                isLoaded: false,
                error: 'Remote config unavailable. Not loading surveys.',
            })
            return logger.warn('Remote config unavailable. Not loading surveys.')''')
replace(p, "            logger.error('PostHog Extensions not found.')", "            this._handleSurveyLoadError('PostHog Extensions not found.')")
replace(p, '''                if (!this._disposed) {
                    callback(result.surveys, result.context)
                }''', '''                if (!this._disposed) {
                    // The cache and receiver definitions are now current, and the request is no
                    // longer in flight. Notify even when a background refresh had a no-op caller.
                    // Deliver errors directly so a failed refresh cannot recursively start a fetch.
                    this._notifyActiveMatchingSurveyCallbacks(result.context)
                    callback(result.surveys, result.context)
                }''')
replace(p, '''        const surveys = (response.json as { surveys?: Survey[] }).surveys || []
        this._registerEventOrActionBasedSurveys(surveys)
''', '''        const surveys = (response.json as { surveys?: Survey[] }).surveys || []
''')
replace(p, '''        client.kv.set({ [SURVEYS]: surveys, [SURVEYS_LOADED_AT]: Date.now() })
        return { surveys, context: { isLoaded: true } }''', '''        client.kv.set({ [SURVEYS]: surveys, [SURVEYS_LOADED_AT]: Date.now() })
        this._registerEventOrActionBasedSurveys(surveys)
        return { surveys, context: { isLoaded: true } }''')
replace(p, '''        if (eventOrActionBasedSurveys.length > 0) {
            this._surveyEventReceiver?.register(eventOrActionBasedSurveys)
        }''', '''        // A refresh replaces the definitions, including an empty list. Do not keep hooks
        // pointing at events/actions that were removed from the latest definitions.
        this._surveyEventReceiver?.replace(eventOrActionBasedSurveys)''')
text = Path(p).read_text()
a = text.index('    onActiveMatchingSurveysChanged(callback: SurveyCallback): () => void {')
b = text.index('    private _getSurveyById', a)
text = text[:a] + '''    onActiveMatchingSurveysChanged(callback: SurveyCallback): () => void {
        if (this._disposed) {
            return () => {}
        }
        const subscription: ActiveMatchingSurveySubscription = { callback, active: true, revision: 0 }
        this._activeMatchingSurveyCallbacks.push(subscription)
        this._startActiveMatchingSurveyConditions()
        if (this._surveyManager) {
            this._notifyActiveMatchingSurveyCallback(subscription)
        }
        return () => {
            subscription.active = false
            this._activeMatchingSurveyCallbacks = this._activeMatchingSurveyCallbacks.filter(
                (current) => current !== subscription
            )
            if (this._activeMatchingSurveyCallbacks.length === 0) {
                this._activeMatchingSurveyConditionsUnsubscribe?.()
                this._activeMatchingSurveyConditionsUnsubscribe = undefined
            }
        }
    }

    private _startActiveMatchingSurveyConditions(): void {
        if (this._surveyManager && this._activeMatchingSurveyCallbacks.length > 0) {
            this._activeMatchingSurveyConditionsUnsubscribe ??= this._configSource.onMatchingConditionsChanged?.(
                this._notifyActiveMatchingSurveyCallbacks
            )
        }
    }

    private _notifyActiveMatchingSurveyCallback(
        subscription: ActiveMatchingSurveySubscription,
        context?: { isLoaded: boolean; error?: string }
    ): void {
        if (this._disposed || !subscription.active) {
            return
        }
        const revision = ++subscription.revision
        const deliver: SurveyCallback = (surveys) => {
            // Removing an entry from the registry cannot cancel an already queued callback.
            // Also discard evaluations superseded by a refresh or a re-entrant capture.
            if (this._disposed || !subscription.active || revision !== subscription.revision) {
                return
            }
            try {
                const resultContext = context ?? { isLoaded: true }
                // Compare the matching definitions and load state, not just activation IDs.
                // A changed URL, flag or definition can change eligibility without re-arming.
                const result = JSON.stringify([surveys, resultContext])
                if (result === subscription.lastResult) {
                    return
                }
                subscription.lastResult = result
                subscription.callback(surveys, resultContext)
            } catch (error) {
                // This guard runs at delivery time, including after an asynchronous fetch.
                logger.error('Error in active matching surveys callback', error)
            }
        }
        try {
            if (context && !context.isLoaded) {
                deliver([])
            } else {
                this.getActiveMatchingSurveys(deliver)
            }
        } catch (error) {
            logger.error('Error in active matching surveys callback', error)
        }
    }

    private _notifyActiveMatchingSurveyCallbacks = (context?: { isLoaded: boolean; error?: string }): void => {
        this._activeMatchingSurveyCallbacks.slice().forEach((subscription) =>
            this._notifyActiveMatchingSurveyCallback(subscription, context)
        )
    }

''' + text[b:]
Path(p).write_text(text)
replace(p, '''            // localStorage is not always available (e.g. in cross-origin iframes); resetting survey state is best-effort.
        }
    }''', '''            // localStorage is not always available (e.g. in cross-origin iframes); resetting survey state is best-effort.
        }
        this._notifyActiveMatchingSurveyCallbacks()
    }''')
replace(p, '''            // localStorage is not always available (e.g. in cross-origin iframes); best-effort only.
        }
    }

    /** Helper method to notify all registered callbacks */''', '''            // localStorage is not always available (e.g. in cross-origin iframes); best-effort only.
        }
        this._notifyActiveMatchingSurveyCallbacks()
    }

    /** Helper method to notify all registered callbacks */''')

p = 'packages/browser/src/utils/event-receiver.ts'
replace(p, '        const previousActivatedIds = this.getActivatedIds()\n', '', count=3)
replace(p, '        this._notifyActivationChanged(previousActivatedIds)', '        this._notifyActivationChanged()', count=3)
replace(p, '''    private _notifyActivationChanged(previousActivatedIds?: string[]): void {
        const activatedIds = this.getActivatedIds()
        if (previousActivatedIds) {
            const activatedIdsChanged =
                activatedIds.length !== previousActivatedIds.length ||
                activatedIds.some((itemId) => !previousActivatedIds.includes(itemId))
            if (!activatedIdsChanged) {
                return
            }
        }
        try {''', '''    private _notifyActivationChanged(): void {
        // Matching eligibility can change even when a repeated trigger leaves the activated
        // IDs unchanged. Subscribers deduplicate the evaluated result instead.
        try {''')
replace(p, '''        if (eventBasedItems.length === 0 && itemsWithCancelEvents.length === 0) {
            return
        }''', '''        if (
            eventBasedItems.length === 0 &&
            itemsWithCancelEvents.length === 0 &&
            !items.some((item) => item.conditions?.actions?.values?.length)
        ) {
            return
        }''')

p = 'packages/browser/src/surveys-config.ts'
replace(p, '''    createEventReceiver(onActivationChanged: () => void): SurveyEventReceiver
}''', '''    createEventReceiver(onActivationChanged: () => void): SurveyEventReceiver
    onMatchingConditionsChanged?(callback: () => void): () => void
}''')
p = 'packages/browser/src/browser-surveys.ts'
replace(p, '''    createEventReceiver(onActivationChanged: () => void): SurveyEventReceiver {
        return new SurveyEventReceiver(this._instance, onActivationChanged)
    }
}''', '''    createEventReceiver(onActivationChanged: () => void): SurveyEventReceiver {
        return new SurveyEventReceiver(this._instance, onActivationChanged)
    }

    onMatchingConditionsChanged(callback: () => void): () => void {
        const unsubscribeCapture = this._instance._addCaptureHook((event) => {
            if (event === '$pageview') {
                callback()
            }
        })
        // onFeatureFlags may synchronously deliver its cached value while registering.
        // The subscription establishes its own initial value after these hooks are attached.
        let listening = false
        const unsubscribeFlags = this._instance.onFeatureFlags(() => {
            if (listening) {
                callback()
            }
        })
        listening = true
        return () => {
            listening = false
            unsubscribeCapture()
            unsubscribeFlags()
        }
    }
}''')

p = 'packages/browser/src/posthog-core.ts'
replace(p, '''     * The listener is called with the initial matching set once surveys are loaded, and again
     * after an event or action activates, cancels, or consumes a survey.''', '''     * The listener receives the initial matching set and updates after event/action triggers,
     * cancellation, consumption, session expiry, definitions refresh, captured pageviews,
     * feature-flag updates, marking a survey as seen, and reset. Unchanged results are suppressed.
     *
     * URL conditions are re-evaluated on captured `$pageview` events, including automatic SPA
     * pageviews when `capture_pageview` is `'history_change'`. With automatic pageviews disabled,
     * capture `$pageview` after navigation. This does not observe arbitrary DOM mutations or time
     * passing; selector, device and wait-period conditions are checked on the supported updates.
     *
     * The optional callback context distinguishes load errors from a successfully loaded empty
     * result. Recoverable load failures keep the subscription alive. Unsubscribing prevents any
     * further delivery, including callbacks from an outstanding initial request.''')

p = 'packages/browser/src/__tests__/posthog-surveys.test.ts'
text = Path(p).read_text()
a = text.index("        describe('onActiveMatchingSurveysChanged', () => {")
b = text.index("        describe('markSurveyAsSeen', () => {", a)
block = text[a:b]
block = block.replace('expect(captureHooks).toHaveLength(2)', 'expect(captureHooks).toHaveLength(3)')
block = block.replace('toHaveBeenLastCalledWith([])', 'toHaveBeenLastCalledWith([], { isLoaded: true })')
block = block.replace('toHaveBeenLastCalledWith([eventSurvey])', 'toHaveBeenLastCalledWith([eventSurvey], { isLoaded: true })')
Path(p).write_text(text[:a] + block + text[b:])

Path('.changeset/fresh-surveys-listen.md').write_text("""---
'posthog-js': minor
'@posthog/types': minor
---

Add `onActiveMatchingSurveysChanged` to observe matching surveys after event/action and survey lifecycle updates, definitions refreshes, captured pageviews, and feature-flag updates. Preserve the one-shot getter, suppress unchanged results, report recoverable load errors through callback context, and prevent delivery after unsubscribe.
""")
print('Applied review fixes. Generated files must be produced by the repository generators.')
