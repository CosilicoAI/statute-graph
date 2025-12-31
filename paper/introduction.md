# Introduction

## The Problem of Statutory Complexity

Tax law is not a collection of independent rules. Each section of the Internal Revenue Code references other sections, creating a web of dependencies that must be understood before any section can be correctly interpreted or encoded into executable form.

Consider the Earned Income Tax Credit (EITC), codified at 26 USC § 32. This single section references:

- Section 1 (tax rates)
- Section 151 (dependency exemption)
- Section 152 (definition of dependent)
- Section 911 (foreign earned income exclusion)
- Section 7703 (marital status)

And many more. To correctly encode Section 32, one must first understand all of these referenced sections. But those sections themselves have dependencies, creating chains that can extend deeply into the code.

## The Encoding Challenge

When translating statute into executable rules (for microsimulation, tax preparation software, or policy analysis), the order of encoding matters:

1. **Forward references** cause problems: If Section A references Section B, encoding A before B requires placeholder logic that must be updated later.

2. **Circular references** require simultaneous encoding: Some sections mutually reference each other, making strict ordering impossible.

3. **Hub sections** block many others: Sections like § 1 (tax rates) are referenced by hundreds of other sections. Encoding these first unblocks the most work.

## Our Contribution

We present a graph-theoretic framework for analyzing statutory cross-references and deriving optimal encoding sequences. Our approach:

1. Parses official US Code XML to extract structured cross-references
2. Models the statute as a directed graph
3. Identifies circular reference groups using strongly connected component (SCC) analysis
4. Produces a topological ordering that respects dependencies while handling cycles

This is, to our knowledge, the first application of dependency graph analysis to statutory encoding order. Prior work on legal citation networks has focused on case law (judicial opinions citing prior decisions) rather than statutory cross-references.
