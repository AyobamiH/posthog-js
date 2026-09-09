from pathlib import Path


def replace(path, before, after, count=1):
    p = Path(path)
    text = p.read_text()
    actual = text.count(before)
    if actual != count:
        raise RuntimeError(f'{path}: expected {count} occurrences, got {actual}: {before[:120]}')
    p.write_text(text.replace(before, after))


# The refresh contract intentionally replaces the receiver definition set so removed
# event/action surveys cannot remain registered after a successful definitions refresh.
p = 'packages/browser/src/__tests__/surveys-extension.test.ts'
replace(
    p,
    """    it('leaves receiver registrations untouched when a refresh has no triggered surveys', async () => {
        const { receiver, source } = createConfigSource({ advancedEnableSurveys: true })
        const { client } = createClient()
        const surveys = new PostHogSurveys(source)
        surveys.setup(client)

        const result = await new Promise<Survey[]>((resolve) => surveys.getSurveys(resolve, true))

        expect(result).toEqual([])
        expect(receiver.register).not.toHaveBeenCalled()
        expect(receiver.replace).not.toHaveBeenCalled()
    })

    it('registers refreshed survey triggers without replacing receiver state', async () => {""",
    """    it('replaces receiver registrations with an empty set when a refresh removes triggered surveys', async () => {
        const { receiver, source } = createConfigSource({ advancedEnableSurveys: true })
        const { client } = createClient()
        const surveys = new PostHogSurveys(source)
        surveys.setup(client)

        const result = await new Promise<Survey[]>((resolve) => surveys.getSurveys(resolve, true))

        expect(result).toEqual([])
        expect(receiver.register).not.toHaveBeenCalled()
        expect(receiver.replace).toHaveBeenCalledTimes(1)
        expect(receiver.replace).toHaveBeenCalledWith([])
    })

    it('replaces receiver registrations with refreshed survey triggers', async () => {""",
)
replace(
    p,
    """        expect(result).toEqual([survey])
        expect(receiver.register).toHaveBeenCalledTimes(1)
        expect(receiver.register).toHaveBeenCalledWith([survey])
        expect(receiver.replace).not.toHaveBeenCalled()
    })""",
    """        expect(result).toEqual([survey])
        expect(receiver.register).not.toHaveBeenCalled()
        expect(receiver.replace).toHaveBeenCalledTimes(1)
        expect(receiver.replace).toHaveBeenCalledWith([survey])
    })""",
)

# Keep @posthog/types aligned with the browser callback contract. Consumers need to be able
# to distinguish a successfully loaded empty result from a recoverable load failure.
p = 'packages/types/src/posthog.ts'
replace(
    p,
    """     * @param callback - Callback to receive the active matching surveys
     * @returns A function to unsubscribe
     */
    onActiveMatchingSurveysChanged(callback: (surveys: any[]) => void): () => void""",
    """     * @param callback - Callback to receive the active matching surveys and optional load context.
     * The context distinguishes a successfully loaded empty result from a load failure.
     * @returns A function to unsubscribe
     */
    onActiveMatchingSurveysChanged(
        callback: (surveys: any[], context?: { isLoaded: boolean; error?: string }) => void
    ): () => void""",
)

# Add an AST-level regression that checks the public @posthog/types callback really exposes
# the second context parameter, rather than only checking that the method name exists.
p = 'packages/types/src/__tests__/posthog-interface.spec.ts'
text = Path(p).read_text()
insert = r'''

    it('exposes load context on the active matching surveys subscription callback', () => {
        const interfacePath = path.resolve(__dirname, '../posthog.ts')
        const program = ts.createProgram([interfacePath], { strictNullChecks: true })
        const sourceFile = program.getSourceFile(interfacePath)
        expect(sourceFile).toBeDefined()

        let callbackType: ts.FunctionTypeNode | undefined
        const visit = (node: ts.Node): void => {
            if (ts.isInterfaceDeclaration(node) && node.name.text === 'PostHog') {
                const method = node.members.find(
                    (member): member is ts.MethodSignature =>
                        ts.isMethodSignature(member) && member.name.getText(sourceFile!) === 'onActiveMatchingSurveysChanged'
                )
                const parameterType = method?.parameters[0]?.type
                if (parameterType && ts.isFunctionTypeNode(parameterType)) {
                    callbackType = parameterType
                }
            }
            ts.forEachChild(node, visit)
        }
        visit(sourceFile!)

        expect(callbackType).toBeDefined()
        expect(callbackType!.parameters).toHaveLength(2)
        const context = callbackType!.parameters[1]
        expect(context.questionToken).toBeDefined()
        expect(context.name.getText(sourceFile!)).toBe('context')
        expect(context.type?.getText(sourceFile!)).toContain('isLoaded: boolean')
        expect(context.type?.getText(sourceFile!)).toContain('error?: string')
    })
'''
needle = "\n})\n"
pos = text.rfind(needle)
if pos == -1:
    raise RuntimeError(f'{p}: could not find describe terminator')
Path(p).write_text(text[:pos] + insert + text[pos:])

print('Applied follow-up fixes for shared refresh expectations and @posthog/types callback context.')
